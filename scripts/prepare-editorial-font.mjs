import {copyFileSync, mkdirSync} from "node:fs";
mkdirSync("public/fonts", {recursive: true});
copyFileSync("node_modules/@fontsource/inter/files/inter-latin-700-normal.woff2", "public/fonts/inter-latin-700-normal.woff2");
copyFileSync("node_modules/@fontsource/inter/LICENSE", "public/fonts/Inter-LICENSE.txt");
