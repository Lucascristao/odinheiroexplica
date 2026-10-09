"""One-off, reviewed graphic fallback for the ODE 2026-10-09 noon recovery.

The ChatGPT cover generated locally could not be transferred to this runner.
Draw the same approved short headline with an illustrative light bulb, not a bill copy.
Identical composition was rendered and inspected by the assistant before this commit.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

W, H, S = 1280, 720, 2
YELLOW = (255, 189, 25)
WHITE = (246, 247, 248)
OUT = Path("production/noticia-2026-10-09-meio-dia/thumbnail.jpg")

def font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in paths:
        if Path(path).is_file():
            return ImageFont.truetype(path, size*S)
    raise FileNotFoundError("Fonte TTF bold indisponível")

def render(path):
    image = Image.new("RGB", (W*S, H*S))
    pixels = image.load()
    for y in range(H*S):
        for x in range(W*S):
            fx, fy = x/(W*S), y/(H*S)
            g = max(0, 1-abs(fx-.82)*1.4-abs(fy-.40)*.6)
            pixels[x,y] = (int(7+11*fx+8*g),int(11+18*fx+12*g),int(17+23*fx+15*g))
    draw = ImageDraw.Draw(image)
    def line(points, fill, width):
        draw.line([(int(x*S),int(y*S)) for x,y in points], fill=fill, width=int(width*S), joint="curve")
    def ellipse(box,fill=None,outline=None,width=1):
        draw.ellipse(tuple(int(a*S) for a in box),fill=fill,outline=outline,width=width*S)
    def rounded(box,r,fill=None,outline=None,width=1):
        draw.rounded_rectangle(tuple(int(a*S) for a in box),radius=r*S,fill=fill,outline=outline,width=width*S)
    rounded((863,125,1175,609),26,(23,33,45),outline=(62,76,82),width=2)
    rounded((901,157,1138,571),17,(30,43,52),outline=(56,67,75),width=1)
    for y in [469,486,503,520,537]:
        line([(937,y),(1102,y)],(63,78,80),2)
    rounded((59,79,69,615),5,YELLOW)
    rounded((93,632,475,640),4,YELLOW)
    glow = Image.new("RGBA", image.size, (0,0,0,0))
    ImageDraw.Draw(glow).ellipse(tuple(int(v*S) for v in (725,125,1181,606)),fill=(255,166,17,108))
    image = Image.alpha_composite(image.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(73*S)))
    draw = ImageDraw.Draw(image)
    def arc(box,start,end,fill,width):
        draw.arc(tuple(int(v*S) for v in box),start,end,fill=fill,width=width*S)
    ellipse((809,164,1107,470),fill=(244,171,41,33),outline=(255,210,120,190),width=7)
    arc((824,179,1092,453),190,340,(255,245,193,245),8)
    arc((821,178,1100,457),18,138,(250,185,62,210),5)
    line([(921,402),(942,449),(961,467)],(255,211,102),5)
    line([(998,402),(981,449),(962,467)],(255,211,102),5)
    for x in [943,956,969,982]:
        line([(x,308),(x,406)],(255,246,178),6)
    for y in [316,346,376]:
        line([(941,y),(986,y)],(255,224,105),3)
    ellipse((929,291,999,325),outline=(255,247,214),width=4)
    rounded((904,467,1014,497),12,(81,88,94),outline=(205,179,115),width=3)
    for y in [503,516,529,542]:
        rounded((912,y,1006,y+6),3,(107,115,122))
    rounded((921,553,998,572),8,(65,73,78))
    for angle in [9,38,136,169,197,265,304]:
        rad = math.radians(angle)
        cx,cy = 960,321
        a = (cx+169*math.cos(rad),cy+177*math.sin(rad))
        b = (cx+188*math.cos(rad),cy+195*math.sin(rad))
        line([a,b], YELLOW,4)
    for title,x,y,size,color in [
        ("QUASE",96,138,77,WHITE),
        ("40%",96,236,143,YELLOW),
        ("VEIO DA",96,427,80,WHITE),
        ("LUZ",96,519,91,WHITE),
    ]:
        draw.text((x*S,y*S),title,font=font(size),fill=color)
    image.convert("RGB").resize((W,H),Image.Resampling.LANCZOS).save(path,"JPEG",quality=92,subsampling=0,optimize=True)

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True,exist_ok=True)
    render(OUT)
    print("ODE_RECOVERY_COVER_READY:",OUT)
