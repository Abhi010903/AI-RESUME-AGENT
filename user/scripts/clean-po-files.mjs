import fs from "node:fs";
import path from "node:path";

const WEB_LOCALES_DIR = "user/apps/web/locales";
const MOBILE_LOCALES_DIR = "user/apps/mobile/locales";

// Strings that MUST be preserved because they describe file format compatibility (Category E)
const PRESERVE_SUBSTRINGS = [
  "This file type can't be imported. Use a PDF, Word, Reactive Resume or JSON Resume file",
  "This JSON isn't a Reactive Resume or JSON Resume file",
  "a Reactive Resume export, then pick up where it left off"
];

function shouldPreserve(str) {
  return PRESERVE_SUBSTRINGS.some(p => str.includes(p));
}

// Exact msgid mappings for web
const EXACT_REPLACEMENTS = [
  ["{stars, plural, one {Star Reactive Resume on GitHub, # star} other {Star Reactive Resume on GitHub, # stars}}", "{stars, plural, one {Star AI Resume Agent on GitHub, # star} other {Star AI Resume Agent on GitHub, # stars}}"],
  ["A backup of this letter. Imports back into Reactive Resume as a letter.", "A backup of this letter. Imports back into AI Resume Agent as a letter."],
  ["A complete backup. Imports back into Reactive Resume.", "A complete backup. Imports back into AI Resume Agent."],
  ["About Reactive Resume", "About AI Resume Agent"],
  ["Couldn't reach Reactive Resume. Check your internet connection, then try again.", "Couldn't reach AI Resume Agent. Check your internet connection, then try again."],
  ["Edit it in Reactive Resume", "Edit it in AI Resume Agent"],
  ["Exchange resume feedback, ask questions, and help shape Reactive Resume with the community.", "Exchange resume feedback, ask questions, and help shape AI Resume Agent with the community."],
  ["For security, only use links from emails sent by Reactive Resume.", "For security, only use links from emails sent by AI Resume Agent."],
  ["Found posting links are read by Reactive Resume and the sites being read.", "Found posting links are read by AI Resume Agent and the sites being read."],
  ["Found posting links are read by Reactive Resume and, when needed, {reader} and the sites being read. The reader may charge.", "Found posting links are read by AI Resume Agent and, when needed, {reader} and the sites being read. The reader may charge."],
  ["Go to Reactive Resume", "Go to AI Resume Agent"],
  ["Good luck out there. Reactive Resume stays free because people chip in.", "Good luck out there. AI Resume Agent is free and open source."],
  ["Is Reactive Resume really free?", "Is AI Resume Agent really free?"],
  ["Link a Reactive Resume (recommended)", "Link an AI Resume Agent resume (recommended)"],
  ["Link a Reactive Resume to use a fit check against each requirement and tailoring.", "Link an AI Resume Agent resume to use a fit check against each requirement and tailoring."],
  ["Made with Reactive Resume", "Made with AI Resume Agent"],
  ["Made with Reactive Resume, free and open source", "Made with AI Resume Agent, free and open source"],
  ["PDF, Word (DOCX), Markdown and JSON. The JSON export imports back into any Reactive Resume, including one you host yourself, so your data is never locked in.", "PDF, Word (DOCX), Markdown and JSON. The JSON export imports back into any AI Resume Agent, including one you host yourself, so your data is never locked in."],
  ["Reactive Resume {__APP_VERSION__} · MIT", "AI Resume Agent {__APP_VERSION__} · MIT"],
  ["Reactive Resume is translated by volunteers.", "AI Resume Agent is translated by volunteers."],
  ["Show “Made with Reactive Resume”", "Show “Made with AI Resume Agent”"],
  ["Star Reactive Resume on GitHub", "Star AI Resume Agent on GitHub"],
  ["Tracked using Reactive Resume", "Tracked using AI Resume Agent"],
  ["Two resumes made with Reactive Resume", "Two resumes made with AI Resume Agent"],
  ["Yes. Reactive Resume is open source under the MIT License and ships as a Docker image, so it runs on your own server with your own database and storage.", "Yes. AI Resume Agent is open source under the MIT License and ships as a Docker image, so it runs on your own server with your own database and storage."],
  // Mobile exact msgids
  ["Allow {0} to use your Reactive Resume?", "Allow {0} to use your AI Resume Agent?"],
  ["Enter the address you open Reactive Resume at in a browser. The app checks it's a Reactive Resume server that allows app sign-in before you continue.", "Enter the address you open AI Resume Agent at in a browser. The app checks it's an AI Resume Agent server that allows app sign-in before you continue."],
  ["Imports back into Reactive Resume", "Imports back into AI Resume Agent"],
  ["No Reactive Resume server answered at this address. Check the spelling, or ask your administrator whether the server allows app sign-in.", "No AI Resume Agent server answered at this address. Check the spelling, or ask your administrator whether the server allows app sign-in."],
  ["The microphone is off for Reactive Resume. Type your answer, or turn it on in Settings.", "The microphone is off for AI Resume Agent. Type your answer, or turn it on in Settings."]
];

function processPoFile(filePath) {
  let content = fs.readFileSync(filePath, "utf8");
  let modified = false;

  // 1. Replace comments
  if (content.includes("appName: Reactive Resume")) {
    content = content.replaceAll("appName: Reactive Resume", "appName: AI Resume Agent");
    modified = true;
  }
  if (content.includes("author: Amruth Pillai, linked")) {
    content = content.replaceAll("author: Amruth Pillai, linked", "appName: AI Resume Agent");
    modified = true;
  }
  if (content.includes("something Reactive Resume doesn't have")) {
    content = content.replaceAll("something Reactive Resume doesn't have", "something AI Resume Agent doesn't have");
    modified = true;
  }

  // 2. Process blocks
  const blocks = content.split(/\n\n+/);
  const updatedBlocks = blocks.map(block => {
    // Check if block contains preserved format compatibility
    if (shouldPreserve(block)) {
      return block;
    }

    let updatedBlock = block;

    // Check exact replacements
    for (const [from, to] of EXACT_REPLACEMENTS) {
      if (updatedBlock.includes(`"${from}"`)) {
        updatedBlock = updatedBlock.replaceAll(`"${from}"`, `"${to}"`);
        // Also if msgstr has translated variation that kept "Reactive Resume"
        // e.g. msgstr "Über Reactive Resume" -> "Über AI Resume Agent"
        if (updatedBlock.includes("Reactive Resume")) {
          // Replace in msgstr lines
          const lines = updatedBlock.split("\n");
          const newLines = lines.map(line => {
            if (line.startsWith("msgstr") && line.includes("Reactive Resume")) {
              return line.replaceAll("Reactive Resume", "AI Resume Agent");
            }
            return line;
          });
          updatedBlock = newLines.join("\n");
        }
        modified = true;
      }
    }

    return updatedBlock;
  });

  if (modified) {
    fs.writeFileSync(filePath, updatedBlocks.join("\n\n") + "\n", "utf8");
    return true;
  }
  return false;
}

let webCount = 0;
for (const file of fs.readdirSync(WEB_LOCALES_DIR)) {
  if (file.endsWith(".po")) {
    if (processPoFile(path.join(WEB_LOCALES_DIR, file))) {
      webCount++;
    }
  }
}

let mobileCount = 0;
for (const file of fs.readdirSync(MOBILE_LOCALES_DIR)) {
  if (file.endsWith(".po")) {
    if (processPoFile(path.join(MOBILE_LOCALES_DIR, file))) {
      mobileCount++;
    }
  }
}

console.log(`Cleaned ${webCount} web PO files and ${mobileCount} mobile PO files.`);
