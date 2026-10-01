import {Landmark, Wallet, UserRound, Search, Bell, LockKeyhole, Check, Undo2, ShieldCheck, TriangleAlert, Clock, Smartphone, Receipt, ShoppingCart, KeyRound, EyeOff, Route, Coins, ChartNoAxesCombined, House, Car, FileText, Globe} from "lucide-react";
import type {StageElement, StageEvent} from "../../src/lib/editorial-stage";
import {svgEmphasis, svgPhase} from "./editorial-svg-motion";

const icons = {bank: Landmark, wallet: Wallet, person: UserRound, search: Search, bell: Bell, lock: LockKeyhole, check: Check, refund: Undo2, shield: ShieldCheck, warning: TriangleAlert, clock: Clock, phone: Smartphone, receipt: Receipt, cart: ShoppingCart, key: KeyRound, "eye-off": EyeOff, route: Route, coins: Coins, chart: ChartNoAxesCombined, house: House, car: Car, document: FileText, globe: Globe};

// Lucide paths inherit these SVG stroke attributes. 90 viewBox units exceed
// every supported contour, so each path is complete at the end of the entrance.
// A faint complete silhouette establishes the subject while its strokes draw.
export const EditorialIcon = ({name, size, color, progress, emphasisProgress = 1, active = false, motion = "draw", actuation, actuationProgress = 1, locked, lockFrom, lockProgress}: {
  name: NonNullable<StageElement["icon"]>;
  size: number;
  color: string;
  progress: number;
  emphasisProgress?: number;
  active?: boolean;
  motion?: "draw" | "none";
  actuation?: StageEvent["actuation"];
  actuationProgress?: number;
  locked?: boolean;
  lockFrom?: boolean;
  lockProgress?: number;
}) => {
  const Icon = icons[name];
  const enter = svgPhase(motion === "none" ? 1 : progress);
  const draw = svgPhase(motion === "none" ? 1 : progress, 0.1, 0.96);
  const emphasis = motion === "none" ? 0 : svgEmphasis(emphasisProgress, active);
  const action = svgPhase(actuationProgress);
  const actionWave = action > 0 && action < 1 ? Math.sin(Math.PI * action) : 0;
  const lockState = locked ?? (actuation === "lock" ? true : actuation === "unlock" ? false : undefined);
  const fromLocked = lockFrom ?? (actuation !== "lock");
  const operatedLock = name === "lock" && lockState !== undefined;
  const opened = (fromLocked ? 0 : 1) + ((lockState ? 0 : 1) - (fromLocked ? 0 : 1)) * svgPhase(lockProgress ?? actuationProgress);
  const shackleAngle = 34 * opened;
  const keyTurn = name === "key" && (actuation === "lock" || actuation === "unlock") ? (actuation === "lock" ? 20 : -20) * actionWave : 0;
  const actionScale = actuation === "tap" ? 1 - actionWave * 0.08 : name === "key" && (actuation === "lock" || actuation === "unlock") ? 1 - actionWave * 0.18 : 1;
  return <div data-svg-motion={motion} data-actuation={actuation} aria-hidden style={{position: "relative", width: size, height: size, flexShrink: 0, color, transform: `scale(${(0.96 + enter * 0.04) * actionScale}) rotate(${keyTurn}deg)`, transformOrigin: "center"}}>
    {operatedLock ? <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke={color} strokeWidth={1.65} strokeLinecap="round" strokeLinejoin="round" style={{position:"absolute",inset:0,opacity:enter}}>
      <rect x="5" y="10" width="14" height="11" rx="2" />
      <path d="M8 10 V7 A4 4 0 0 1 16 7 V10" transform={`rotate(${shackleAngle} 16 10)`} />
      <circle cx="12" cy="15" r="1" /><path d="M12 16 V18" />
    </svg> : <>
      <Icon size={size} strokeWidth={1.65} style={{position: "absolute", inset: 0, opacity: 0.16 * enter * (1 - draw)}} />
      <Icon size={size} strokeWidth={1.65} strokeDasharray={90} strokeDashoffset={90 * (1 - draw)} style={{position: "absolute", inset: 0}} />
      {emphasis > 0 && <Icon size={size} strokeWidth={2.55} style={{position: "absolute", inset: 0, opacity: emphasis * 0.55}} />}
    </>}
    {actuation && <svg viewBox="0 0 24 24" width={size} height={size} style={{position:"absolute",inset:0}} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      {actuation === "tap" && actionWave > 0 && <><circle cx="17" cy="16" r={1 + actionWave * 4} opacity={actionWave} /><path d="M21 21 L17 16" opacity={actionWave} /></>}
      {actuation === "confirm" && action > 0 && <><circle cx="18" cy="18" r="4.5" fill="#142126" stroke={color} /><path d="M15.8 18 L17.3 19.5 L20.3 16.2" pathLength={1} strokeDasharray={1} strokeDashoffset={1-action} /></>}
      {actuation === "signal" && actionWave > 0 && <g opacity={actionWave}><path d="M4 6 Q1 12 4 18 M20 6 Q23 12 20 18" pathLength={1} strokeDasharray={1} strokeDashoffset={1-action} /></g>}
      {actuation === "count" && name === "coins" && actionWave > 0 && <circle cx="17" cy={8-actionWave*3} r="3.5" fill="#142126" opacity={actionWave} />}
    </svg>}
  </div>;
};
