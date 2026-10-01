import {AbsoluteFill, Composition, Sequence, registerRoot} from "remotion";
import {editorialStageSchema, type StageEvent} from "../../src/lib/editorial-stage";
import {EditorialStage} from "./EditorialStage";
import {engineMotionFixtures} from "./engine-motion-fixtures";

const EngineMotionReview = () => <AbsoluteFill style={{background: "#101317"}}>
  {engineMotionFixtures.map((scene, index) => <Sequence key={scene.id} from={index * 300} durationInFrames={300}>
    <EditorialStage stage={editorialStageSchema.parse(scene.visual.stage)} beats={scene.visual.beats as StageEvent[]} title={scene.title}/>
  </Sequence>)}
</AbsoluteFill>;

registerRoot(() => <Composition id="EngineMotionReview" component={EngineMotionReview} durationInFrames={600} fps={30} width={1920} height={1080}/>);
