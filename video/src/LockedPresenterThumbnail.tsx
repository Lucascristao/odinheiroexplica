import React from "react";
import {AbsoluteFill, Img, Still, registerRoot} from "remotion";
import "@fontsource/inter/900.css";

export type LockedCoverProps = {headline:string; portrait:string; background:string; portraitSide:"left"|"right";
  headlinePosition:"upper"|"middle"|"lower"; portraitSize:"compact"|"standard"|"close"};
export const LockedPresenterThumbnail:React.FC<LockedCoverProps> = ({headline,portrait,background,portraitSide,headlinePosition,portraitSize}) => {
  const portraitLeft=portraitSide==="left";
  const words=headline.trim().split(/\s+/);
  const split=Math.ceil(words.length/2);
  const lines=[words.slice(0,split).join(" "),words.slice(split).join(" ")].filter(Boolean);
  const longest=Math.max(...lines.map(line=>line.length));
  const fontSize=Math.min(94,Math.max(52,Math.floor(640/(longest*.65))));
  return <AbsoluteFill style={{backgroundColor:"#090B0D",overflow:"hidden",fontFamily:"Inter,Arial,sans-serif"}}>
    <Img src={background} style={{width:"100%",height:"100%",objectFit:"cover"}} />
    <AbsoluteFill style={{background:"linear-gradient(0deg,rgba(9,11,13,.85) 0%,rgba(9,11,13,.22) 38%,transparent 68%)"}} />
    <Img src={portrait} style={{position:"absolute",height:{compact:480,standard:560,close:664}[portraitSize],bottom:0,
      ...(portraitLeft?{left:-26}:{right:-26}),objectFit:"contain"}} />
    <div style={{position:"absolute",top:{upper:70,middle:240,lower:450}[headlinePosition],width:620,...(portraitLeft?{right:42}:{left:42}),
      color:"#FFBD19",fontWeight:900,fontSize,lineHeight:1.03,letterSpacing:0,
      textShadow:"0 4px 22px rgba(0,0,0,.8)",padding:"18px 0"}}>
      {lines.map((line,index)=><div key={index}>{line}</div>)}
    </div>
  </AbsoluteFill>;
};

const Root=()=> <Still id="LockedPresenterThumbnail" component={LockedPresenterThumbnail}
  width={1280} height={720} defaultProps={{headline:"ROBERTO",portrait:"",background:"",portraitSide:"right" as const,
    headlinePosition:"lower" as const,portraitSize:"close" as const}} />;
registerRoot(Root);
