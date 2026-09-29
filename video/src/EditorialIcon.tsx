import {Landmark, Wallet, UserRound, Search, Bell, LockKeyhole, Check, Undo2, ShieldCheck, TriangleAlert, Clock, Smartphone, Receipt, ShoppingCart, KeyRound, EyeOff, Route, Coins, ChartNoAxesCombined, House, Car, FileText, Globe} from "lucide-react";
import type {StageElement} from "../../src/lib/editorial-stage";

const icons = {bank: Landmark, wallet: Wallet, person: UserRound, search: Search, bell: Bell, lock: LockKeyhole, check: Check, refund: Undo2, shield: ShieldCheck, warning: TriangleAlert, clock: Clock, phone: Smartphone, receipt: Receipt, cart: ShoppingCart, key: KeyRound, "eye-off": EyeOff, route: Route, coins: Coins, chart: ChartNoAxesCombined, house: House, car: Car, document: FileText, globe: Globe};

// Local SVGs: no remote icon service, animation loop, emoji or raster dependency.
export const EditorialIcon = ({name, size, color, progress}: {name: NonNullable<StageElement["icon"]>; size: number; color: string; progress: number}) => {
  const Icon = icons[name];
  return <div style={{width: size, height: size, flexShrink: 0, color, transform: `scale(${0.92 + progress * 0.08})`, transformOrigin: "center"}}>
    <Icon size={size} strokeWidth={1.65} />
  </div>;
};
