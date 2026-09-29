import {z} from "zod";

export const regionSchema = z.object({x: z.number().min(0).max(100), y: z.number().min(0).max(100), width: z.number().min(1).max(100), height: z.number().min(1).max(100)}).refine(r => r.x+r.width<=100 && r.y+r.height<=100, "Região fora da imagem.");
export const annotationSchema = z.object({id: z.string().min(1), style: z.enum(["highlight", "underline", "strike", "circle"]), region: regionSchema});
export const emphasisSchema = z.object({phrase: z.string().min(1).max(80), style: z.enum(["highlight", "underline", "strike"])});
export const chartSchema = z.object({
  type: z.enum(["line", "bar"]),
  source_id: z.string().min(1),
  unit: z.string().min(1).max(24),
  x_label: z.string().min(1).max(36),
  y_min: z.number().finite(), y_max: z.number().finite(),
  points: z.array(z.object({x: z.number().finite(), label: z.string().min(1).max(20), value: z.number().finite()})).min(2).max(40),
}).superRefine((c,ctx)=>{
  if(c.y_max<=c.y_min)ctx.addIssue({code:"custom",message:"Escala precisa crescer."});
  if(c.type==="bar" && c.y_min!==0)ctx.addIssue({code:"custom",message:"Barras partem de zero."});
  c.points.forEach((p,i)=>{
    if(p.value<c.y_min||p.value>c.y_max)ctx.addIssue({code:"custom",message:"Valor fora da escala declarada."});
    if(i && p.x<=c.points[i-1].x)ctx.addIssue({code:"custom",message:"Coordenadas X devem crescer sem duplicatas."});
  });
});
export type Region = z.infer<typeof regionSchema>;
export type Chart = z.infer<typeof chartSchema>;
export type Emphasis = z.infer<typeof emphasisSchema>;
export const fullView: Region = {x:0,y:0,width:100,height:100};
