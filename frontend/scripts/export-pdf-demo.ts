/**
 * Démo/vérification visuelle : génère un PDF depuis un batch factice
 * (4 leçons : contenu riche, prompts complets, video manquant, media absent).
 * Usage: npx esbuild scripts/export-pdf-demo.ts --bundle --platform=node
 *        --format=cjs --outfile=../test-artifacts/demo.cjs && node ../test-artifacts/demo.cjs
 */
import { writeFileSync, mkdirSync } from "fs";
import * as path from "path";
import { buildAIFactoryPdf, aiFactoryExportFileName } from "../src/utils/exportAIFactoryPdf";

const longParagraph =
  "La photosynthèse est le processus bioénergétique par lequel les plantes vertes synthétisent " +
  "de la matière organique à partir du dioxyde de carbone atmosphérique et de l'eau, en utilisant " +
  "la lumière du soleil comme source d'énergie. Ce processus se déroule dans les chloroplastes, " +
  "organites cellulaires contenant un pigment essentiel : la chlorophylle. **Point clé :** sans " +
  "la photosynthèse, l'atmosphère terrestre ne contiendrait presque pas d'oxygène libre.";

const bundle = {
  plan: {
    title: "La Photosynthèse — Sciences Naturelles",
    level: "beginner",
    category: "Sciences",
    modules: [
      {
        title: "Fondamentaux",
        lessons: [{ title: "Qu'est-ce que la photosynthèse ?" }, { title: "La chlorophylle et la lumière" }],
      },
      {
        title: "Applications",
        lessons: [{ title: "Équation bilan de la réaction" }, { title: "Facteurs limitants" }],
      },
    ],
  },
  lessons: {
    "Fondamentaux::Qu'est-ce que la photosynthèse ?": `# Introduction\n\n${longParagraph}\n\n## Les deux phases\n\n### Phase claire\n\nLa phase photochimique se produit dans les membranes des thylakoïdes :\n\n- Absorption de la lumière par la chlorophylle\n- Photolyse de l'eau (libération d'oxygène)\n- Production d'ATP et de NADPH\n\n1. Capture photonique\n2. Transport d'électrons\n3. Synthèse d'ATP\n\n> La lumière est le facteur énergétique premier de toute la chaîne.\n\n## Conclusion\n\nCe mécanisme universel alimente presque tous les écosystèmes terrestres.`,
    "Fondamentaux::La chlorophylle et la lumière": `## Le spectre d'absorption\n\nLa chlorophylle absorbe principalement le bleu et le rouge :\n\n| Zone | Absorption |\n|------|-----------|\n| Bleu | forte |\n| Vert | faible (réfléchi) |\n\n**Remarque :** c'est pourquoi les feuilles paraissent vertes.`,
    "Applications::Équation bilan de la réaction": `## Équation globale\n\n6 CO₂ + 6 H₂O → C₆H₁₂O₆ + 6 O₂\n\nCette équation résume l'ensemble du processus décrit précédemment.`,
    "Applications::Facteurs limitants": `Les trois facteurs limitants principaux sont l'intensité lumineuse, la concentration en CO₂ et la température.`,
  },
  media_prompts: {
    "Fondamentaux::Qu'est-ce que la photosynthèse ?": {
      image_prompt:
        "Cross-section illustration of a green leaf cell showing chloroplasts, sunlight rays entering from top-left, water molecules and CO2 particles, educational diagram style, soft colors, clean labels",
      video_prompt:
        "Animated explainer video: camera slowly zooms into a green leaf, transitions to cellular view, chloroplasts glowing as light beams convert water and CO2 into glucose, calm documentary narration tone, 60 seconds",
    },
    "Fondamentaux::La chlorophylle et la lumière": {
      image_prompt:
        "Scientific chart of chlorophyll absorption spectrum, blue and red peaks highlighted, green valley visible, minimalist flat design on white background",
      video_prompt: "",
    },
    "Applications::Équation bilan de la réaction": {},
    "Applications::Facteurs limitants": {
      image_prompt: "Three panels showing plants under low light, low CO2, extreme temperature",
      video_prompt: "Time-lapse of plant growth under varying light conditions, split screen, 30 seconds",
    },
  } as any,
};

const outDir = path.resolve(__dirname, "../test-artifacts");
mkdirSync(outDir, { recursive: true });
const doc = buildAIFactoryPdf(bundle);
const name = aiFactoryExportFileName();
writeFileSync(path.join(outDir, name), Buffer.from(doc.output("arraybuffer")));
console.log("OK ->", path.join(outDir, name));
