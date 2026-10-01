import {useEffect, useState} from "react";
import {cancelRender, continueRender, delayRender, staticFile} from "remotion";
import {loadFont} from "@remotion/fonts";
import {measureText} from "@remotion/layout-utils";
import {EDITORIAL_FONT} from "../../src/lib/editorial-typography";

let fontPromise: Promise<unknown> | undefined;
export function useEditorialFont() {
  const [handle]=useState(()=>delayRender("Loading canonical editorial font"));
  const [ready,setReady]=useState(false);
  useEffect(()=> {
    fontPromise??=loadFont({family:EDITORIAL_FONT,url:staticFile("fonts/inter-latin-700-normal.woff2"),weight:"700"});
    fontPromise.then(()=>{setReady(true);continueRender(handle);}).catch(cancelRender);
  },[handle]);
  return ready;
}
export const measureEditorialText = (text:string,size:number) => measureText({text,fontFamily:EDITORIAL_FONT,fontSize:size,fontWeight:700,letterSpacing:"0px",validateFontIsLoaded:true}).width;
