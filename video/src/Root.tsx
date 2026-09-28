import {Composition} from "remotion";
import {BrandMotionTest} from "./BrandMotionTest";

export const RemotionRoot = () => {
  return (
    <Composition
      id="BrandMotionTest"
      component={BrandMotionTest}
      durationInFrames={810}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
