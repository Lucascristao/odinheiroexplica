import type {Region} from "./editorial-evidence";

/** Establish a real source page before approaching the speech-bound region. */
export function newsDocumentContext(view:Region,seconds:number|undefined,frame:number,fps:number) {
  const contextFrames=(seconds??0)*fps;
  const progress=contextFrames>0?Math.max(0,Math.min(1,(frame-contextFrames)/Math.max(1,.6*fps))):1;
  return {progress,showContext:contextFrames>0 && frame<contextFrames,view:{x:view.x*progress,y:view.y*progress,
    width:100+(view.width-100)*progress,height:100+(view.height-100)*progress}};
}
