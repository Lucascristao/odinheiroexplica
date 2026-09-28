import {AbsoluteFill} from "remotion";
import project from "../data/daily.json";

const BG = "#090b0d";
const SURFACE = "#12161a";
const GOLD = "#ffbd19";
const WHITE = "#f6f7f8";
const MUTED = "#9ba4ae";
const RED = "#ff6b6b";
const FONT = "Arial, Helvetica, sans-serif";

export const DailyThumbnail = () => {
  const headline =
    project.packaging?.thumbnails?.[0]?.headline ?? "SEU SALDO VOLTA?";
  const words = headline.split(/\s+/);
  const top = words.slice(0, Math.max(1, words.length - 1)).join(" ");
  const bottom = words.slice(-1).join(" ");

  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        fontFamily: FONT,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 58,
          top: 46,
          color: GOLD,
          fontSize: 20,
          fontWeight: 950,
          letterSpacing: 4,
        }}
      >
        O DINHEIRO EXPLICA
      </div>

      <div
        style={{
          position: "absolute",
          left: 62,
          top: 145,
          width: 610,
          color: WHITE,
          lineHeight: 0.92,
          letterSpacing: -5,
          fontWeight: 950,
        }}
      >
        <div style={{fontSize: 68}}>{top}</div>
        <div style={{fontSize: 112, color: GOLD, marginTop: 12}}>{bottom}</div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 66,
          top: 410,
          display: "inline-flex",
          alignItems: "center",
          padding: "11px 16px",
          borderRadius: 999,
          background: "rgba(255,107,107,.10)",
          border: "1px solid rgba(255,107,107,.36)",
          color: "#ff9898",
          fontSize: 18,
          fontWeight: 900,
          letterSpacing: 2,
        }}
      >
        BETS PROIBIDAS
      </div>

      <div
        style={{
          position: "absolute",
          left: 66,
          top: 470,
          width: 540,
          color: MUTED,
          fontSize: 23,
          lineHeight: 1.35,
          fontWeight: 750,
        }}
      >
        O que acontece com o dinheiro que ficou na plataforma?
      </div>

      <div
        style={{
          position: "absolute",
          right: 325,
          top: 110,
          width: 315,
          height: 505,
          borderRadius: 42,
          background: "#0d1115",
          border: "2px solid #313840",
          boxShadow: "0 28px 70px rgba(0,0,0,.48)",
          transform: "rotate(-3deg)",
        }}
      >
        <div
          style={{
            height: 54,
            borderBottom: "1px solid #2c333a",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: MUTED,
            fontSize: 15,
            fontWeight: 850,
            letterSpacing: 2,
          }}
        >
          PLATAFORMA
        </div>

        <div
          style={{
            margin: "34px 28px 0",
            padding: "28px 24px",
            borderRadius: 24,
            background: SURFACE,
            border: "1px solid #2f363d",
          }}
        >
          <div
            style={{
              color: MUTED,
              fontSize: 16,
              fontWeight: 800,
              letterSpacing: 1.5,
            }}
          >
            SALDO DISPONÍVEL
          </div>
          <div
            style={{
              color: WHITE,
              fontSize: 56,
              fontWeight: 950,
              marginTop: 12,
              letterSpacing: -3,
            }}
          >
            R$ ...
          </div>
          <div
            style={{
              marginTop: 24,
              height: 54,
              borderRadius: 14,
              display: "grid",
              placeItems: "center",
              background: GOLD,
              color: BG,
              fontSize: 17,
              fontWeight: 950,
            }}
          >
            RESGATE
          </div>
        </div>

        <div
          style={{
            margin: "28px 28px 0",
            color: RED,
            fontSize: 18,
            fontWeight: 900,
            lineHeight: 1.25,
          }}
        >
          novos aportes bloqueados
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          right: 200,
          top: 310,
          width: 120,
          height: 12,
          borderRadius: 999,
          background: GOLD,
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 184,
          top: 294,
          width: 0,
          height: 0,
          borderTop: "22px solid transparent",
          borderBottom: "22px solid transparent",
          borderLeft: "34px solid #ffbd19",
        }}
      />

      <div
        style={{
          position: "absolute",
          right: 38,
          top: 242,
          width: 155,
          height: 160,
          borderRadius: 28,
          background: SURFACE,
          border: "1px solid #353c44",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 20px 45px rgba(0,0,0,.35)",
        }}
      >
        <div style={{fontSize: 38, color: GOLD, fontWeight: 950}}>R$</div>
        <div
          style={{
            marginTop: 10,
            color: WHITE,
            fontSize: 18,
            fontWeight: 900,
            letterSpacing: 1,
            textAlign: "center",
          }}
        >
          SUA CONTA
        </div>
      </div>
    </AbsoluteFill>
  );
};
