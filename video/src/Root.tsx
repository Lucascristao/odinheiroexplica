import {Composition} from "remotion";
import {BrandMotionTest} from "./BrandMotionTest";
import {DynamicVideo} from "./DynamicVideo";
import {DynamicMotionV2} from "./DynamicMotionV2";
import renderInput from "../generated/render-input.json";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="BrandMotionTest"
        component={BrandMotionTest}
        durationInFrames={810}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="DynamicVideo"
        component={DynamicVideo}
        durationInFrames={renderInput.duration_in_frames}
        fps={renderInput.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="DynamicMotionV2"
        component={DynamicMotionV2}
        durationInFrames={810}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
