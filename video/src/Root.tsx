import {Composition, Still} from "remotion";
import {BrandMotionTest} from "./BrandMotionTest";
import {DynamicVideo} from "./DynamicVideo";
import {DynamicMotionV2} from "./DynamicMotionV2";
import {EditorialPilot, PixPilotThumbnail} from "./EditorialPilot";\nimport {DailyEditorial} from "./DailyEditorial";\nimport {DailyThumbnail} from "./DailyThumbnail";
import renderInput from "../generated/render-input.json";
import pilotRenderInput from "../generated/pilot-render-input.json";\nimport dailyRenderInput from "../generated/daily-render-input.json";

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
      <Composition
        id="EditorialPilot"
        component={EditorialPilot}
        durationInFrames={pilotRenderInput.duration_in_frames}
        fps={pilotRenderInput.fps}
        width={1920}
        height={1080}
      />
      <Still
        id="PixPilotThumbnail"
        component={PixPilotThumbnail}
        defaultProps={{variant: "A"}}
        width={1280}
        height={720}
      />
    </>
  );
};
