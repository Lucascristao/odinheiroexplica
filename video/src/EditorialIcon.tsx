import {Landmark, Wallet, UserRound, Search, Bell, LockKeyhole, Check, Undo2, ShieldCheck, TriangleAlert, Clock, Smartphone, Receipt, ShoppingCart, KeyRound, EyeOff, Route, Coins, ChartNoAxesCombined, House, Car, FileText, Globe} from "lucide-react";
import type {StageElement} from "../../src/lib/editorial-stage";
import {svgEmphasis, svgPhase} from "./editorial-svg-motion";

const icons = {bank: Landmark, wallet: Wallet, person: UserRound, search: Search, bell: Bell, lock: LockKeyhole, check: Check, refund: Undo2, shield: ShieldCheck, warning: TriangleAlert, clock: Clock, phone: Smartphone, receipt: Receipt, cart: ShoppingCart, key: KeyRound, "eye-off": EyeOff, route: Route, coins: Coins, chart: ChartNoAxesCombined, house: House, car: Car, document: FileText, globe: Globe};

// Lucide paths inherit these SVG stroke attributes. 90 viewBox units exceed
// every supported contour, so each path is complete at the end of the entrance.
// A faint complete silhouette establishes the subject while its strokes draw.
export const EditorialIcon = ({name, size, color, progress, emphasisProgress = 1, active = false, motion = "draw"}: {
  name: NonNullable<StageElement["icon"]>;
  size: number;
  color: string;
  progress: number;
  emphasisProgress?: number;
  active?: boolean;
  motion?: "draw" | "none";
}) => {
  const Icon = icons[name];
  const enter = svgPhase(motion === "none" ? 1 : progress);
  const draw = svgPhase(motion === "none" ? 1 : progress, 0.1, 0.96);
  const emphasis = motion === "none" ? 0 : svgEmphasis(emphasisProgress, active);
  return <div data-svg-motion={motion} aria-hidden style={{position: "relative", width: size, height: size, flexShrink: 0, color, transform: `scale(${0.96 + enter * 0.04})`, transformOrigin: "center"}}>
    <Icon size={size} strokeWidth={1.65} style={{position: "absolute", inset: 0, opacity: 0.16 * enter * (1 - draw)}} />
    <Icon size={size} strokeWidth={1.65} strokeDasharray={90} strokeDashoffset={90 * (1 - draw)} style={{position: "absolute", inset: 0}} />
    {emphasis > 0 && <Icon size={size} strokeWidth={2.55} style={{position: "absolute", inset: 0, opacity: emphasis * 0.55}} />}
  </div>;
};
