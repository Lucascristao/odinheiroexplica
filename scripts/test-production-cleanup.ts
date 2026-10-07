import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync} from "node:fs";
import {resolve, join} from "node:path";
import {cleanupCompletedProduction, registerTemporaryPaths} from "./production-cleanup";

// These fixtures exercise deletion boundaries using disposable files, never the checkout's outputs.
const checkout = resolve(import.meta.dirname, "..");
mkdirSync(join(checkout, "work"), {recursive: true});
const suiteRoot = mkdtempSync(join(checkout, "work", "cleanup-test-"));
const projectId = "cleanup-example-2026-10-07";
const production = "production/cleanup-example-2026-10-07";
const folderId = "verified-drive-folder";
const videoContent = "temporary video";
const videoHash = createHash("sha256").update(videoContent).digest("hex");
const reviewContent = "Final review in Git";
const reviewHash = createHash("sha256").update(reviewContent).digest("hex");
let passed = 0;

function write(root: string, relative: string, value: unknown): void {
  const path = resolve(root, relative);
  mkdirSync(resolve(path, ".."), {recursive: true});
  writeFileSync(path, typeof value === "string" ? value : JSON.stringify(value, null, 2) + "\n");
}

function fixture(name: string) {
  const root = join(suiteRoot, name);
  const project = {project_id: projectId, title: "Vídeo de exemplo", scenes: []};
  const source = JSON.stringify(project, null, 2) + "\n";
  const sourceHash = createHash("sha256").update(source.replace(/\r\n/g, "\n")).digest("hex");
  const files = [
    {id: "video-id", name: "daily-video.mp4", role: "video", size: String(Buffer.byteLength(videoContent)), sha256: videoHash},
    {id: "metadata-id", name: "daily-youtube.json", role: "metadata", size: "100"},
    {id: "text-id", name: "daily-youtube.txt", role: "publication_text", size: "100"},
    {id: "package-id", name: "daily-visual-review.zip", role: "visual_review", size: "100"},
    {id: "cover-id", name: "thumbnail-abcdef123456.jpg", role: "thumbnail", size: "100"},
    {id: "review-id", name: `editorial-review-${reviewHash.slice(0, 12)}.md`, role: "editorial-review", size: "100"},
  ];
  const final = {complete_package: true, project_id: projectId, source_project_sha256: sourceHash,
    folder_id: folderId, folder_url: `https://drive.google.com/drive/folders/${folderId}`, files,
    source_run_id: 101, delivery_run_id: 102, supplement_runs: {thumbnail: 103, editorial_review: 104}};
  write(root, "video/data/daily.json", source);
  write(root, `${production}/final-delivery.json`, final);
  write(root, `${production}/delivery.json`, {folder_id: folderId, files: {
    video: {file_id: "video-id", name: "daily-video.mp4", sha256: videoHash, size_bytes: Buffer.byteLength(videoContent)},
    metadata: {file_id: "metadata-id", name: "daily-youtube.json", size_bytes: 100},
    publication_text: {file_id: "text-id", name: "daily-youtube.txt", size_bytes: 100},
    visual_review: {file_id: "package-id", name: "daily-visual-review.zip", size_bytes: 100},
  }});
  const resume = {source_run_id: 101, source_project_sha256: sourceHash, project_sha256: sourceHash,
    project_id: projectId, video_sha256: videoHash, new_synthesis: false, new_render: false};
  write(root, `${production}/resume-receipt.json`, resume);
  write(root, "work/runs/101/video/data/daily.json", source);
  write(root, "work/runs/101/render-output/daily-video.mp4", videoContent);
  write(root, "work/runs/102/video/generated/daily-resume-receipt.json", resume);
  write(root, "work/runs/102/render-output/daily-video.mp4", videoContent);
  write(root, "work/runs/999/video/generated/daily-project.json", {project_id: "other-episode", title: "Other"});
  write(root, "work/runs/999/keep.txt", "other episode");
  write(root, "work/python-deps/keep.txt", "dependencies");
  write(root, "work/unrelated.txt", "unrelated scratch work");
  write(root, `${production}/review.md`, reviewContent);
  write(root, "scripts/permanent-test.ts", "Permanent test source");
  return {root, final, sourceHash};
}

function test(name: string, action: () => void) {
  action();
  passed += 1;
  console.log(`✓ ${name}`);
}

function keepTemporary(root: string) {
  assert.equal(existsSync(join(root, "work/runs/101/render-output/daily-video.mp4")), true,
    "A refused cleanup must leave its candidate files intact");
}

try {
  test("An incomplete Drive package does not remove local media", () => {
    const f = fixture("incomplete");
    write(f.root, `${production}/final-delivery.json`, {...f.final, complete_package: false});
    assert.throws(() => cleanupCompletedProduction(f.root, production, {trackedFiles: []}));
    keepTemporary(f.root);
  });

  test("A different episode's receipt cannot authorize deletion", () => {
    const f = fixture("project-mismatch");
    write(f.root, `${production}/final-delivery.json`, {...f.final, project_id: "wrong-episode"});
    assert.throws(() => cleanupCompletedProduction(f.root, production, {trackedFiles: []}));
    keepTemporary(f.root);
  });

  test("A changed current project invalidates the old completion receipt", () => {
    const f = fixture("hash-mismatch");
    write(f.root, "video/data/daily.json", {project_id: projectId, title: "Changed script", scenes: []});
    assert.throws(() => cleanupCompletedProduction(f.root, production, {trackedFiles: []}));
    keepTemporary(f.root);
  });

  test("A missing final cover leaves temporary files available for completing delivery", () => {
    const f = fixture("missing-cover");
    write(f.root, `${production}/final-delivery.json`, {...f.final, files: f.final.files.filter(file => file.role !== "thumbnail")});
    assert.throws(() => cleanupCompletedProduction(f.root, production, {trackedFiles: []}));
    keepTemporary(f.root);
  });

  test("An older review in Drive does not authorize deleting files for the revised review", () => {
    const f = fixture("old-review-version");
    write(f.root, `${production}/review.md`, "Review changed after its upload");
    assert.throws(() => cleanupCompletedProduction(f.root, production, {trackedFiles: []}));
    keepTemporary(f.root);
  });

  test("A replaced video in the final Drive receipt cannot authorize deleting the original local render", () => {
    const f = fixture("remote-replaced-video");
    const files = f.final.files.map(file => file.role === "video" ? {...file, id: "replacement-video-id"} : file);
    write(f.root, `${production}/final-delivery.json`, {...f.final, files});
    assert.throws(() => cleanupCompletedProduction(f.root, production, {trackedFiles: []}));
    keepTemporary(f.root);
  });

  test("A corrupted resumed MP4 aborts the whole deletion plan before the original run is removed", () => {
    const f = fixture("corrupt-resumed-video");
    write(f.root, "work/runs/102/render-output/daily-video.mp4", "Changed resumed video despite the old checksum receipt");
    assert.throws(() => cleanupCompletedProduction(f.root, production, {trackedFiles: []}));
    keepTemporary(f.root);
    assert.equal(existsSync(join(f.root, "work/runs/102/render-output/daily-video.mp4")), true);
  });

  test("A metadata-only recovery download can be removed using its valid original render receipt", () => {
    const f = fixture("metadata-only-recovery");
    const downloadedVideo = join(f.root, "work/runs/102/render-output/daily-video.mp4");
    assert.ok(downloadedVideo.startsWith(suiteRoot + (process.platform === "win32" ? "\\" : "/")));
    rmSync(downloadedVideo);
    const result = cleanupCompletedProduction(f.root, production, {trackedFiles: []});
    assert.equal(result.status, "complete");
    assert.equal(existsSync(join(f.root, "work/runs/102")), false);
    assert.equal(existsSync(join(f.root, `${production}/resume-receipt.json`)), true);
    assert.equal(existsSync(join(f.root, "work/runs/999/keep.txt")), true);
  });

  test("Optional review extraction does not require a ZIP to finish cleanup", () => {
    const f = fixture("optional-review-zip");
    write(f.root, `${production}/final-delivery.json`, {...f.final, files: f.final.files.filter(file => file.role !== "visual_review")});
    const result = cleanupCompletedProduction(f.root, production, {trackedFiles: []});
    assert.equal(result.status, "complete");
    assert.equal(existsSync(join(f.root, "work/runs/101")), false);
  });

  test("Windows CRLF and LF represent the same project for verified cleanup", () => {
    const f = fixture("windows-line-endings");
    const path = join(f.root, "video/data/daily.json");
    writeFileSync(path, readFileSync(path, "utf8").replace(/\n/g, "\r\n"));
    const result = cleanupCompletedProduction(f.root, production, {trackedFiles: []});
    assert.equal(result.status, "complete");
    assert.equal(existsSync(join(f.root, "work/runs/101")), false);
  });

  test("Verified supplemental receipts remove their downloads but an unrelated folder receipt does not", () => {
    const f = fixture("supplement-downloads");
    const receipt = {verified_readback: true, project_id: projectId, source_project_sha256: f.sourceHash,
      folder: {id: folderId}, role: "thumbnail", file: {id: "cover-id", name: "thumbnail-abcdef123456.jpg"}};
    write(f.root, "work/runs/103/daily-supplement-drive.json", receipt);
    write(f.root, "work/runs/103/temporary.txt", "Downloaded supplement receipt");
    write(f.root, "work/runs/998/daily-supplement-drive.json", {...receipt, folder: {id: "another-drive-folder"}});
    write(f.root, "work/runs/998/keep.txt", "Unrelated supplement");
    const result = cleanupCompletedProduction(f.root, production, {trackedFiles: []});
    assert.equal(result.status, "complete");
    assert.equal(existsSync(join(f.root, "work/runs/103")), false);
    assert.equal(existsSync(join(f.root, "work/runs/998/keep.txt")), true);
  });

  test("Registered generated outputs are cleaned while unregistered files and dependencies survive", () => {
    const f = fixture("registered-generated-output");
    const owned = "public/generated-clips/this-episode.mp4";
    const unrelated = "public/generated-clips/other-episode.mp4";
    write(f.root, owned, "Disposable generated clip");
    write(f.root, unrelated, "Unregistered clip");
    registerTemporaryPaths(f.root, [owned]);
    const result = cleanupCompletedProduction(f.root, production, {trackedFiles: []});
    assert.equal(result.status, "complete");
    assert.equal(existsSync(join(f.root, owned)), false);
    assert.equal(existsSync(join(f.root, unrelated)), true);
    assert.equal(existsSync(join(f.root, "work/python-deps/keep.txt")), true);
    assert.throws(() => registerTemporaryPaths(f.root, ["production/cleanup-example-2026-10-07/review.md"]));
    assert.throws(() => registerTemporaryPaths(f.root, ["public/generated-clips/../fonts/permanent.ttf"]));
  });

  test("A Windows backslash traversal cannot register an untracked final asset as temporary", () => {
    const f = fixture("windows-registry-traversal");
    const finalAsset = "production/final-untracked.png";
    write(f.root, finalAsset, "Final asset outside the temporary output directory");
    assert.throws(() => registerTemporaryPaths(f.root, ["render-output/..\\production\\final-untracked.png"]));
    assert.equal(existsSync(join(f.root, finalAsset)), true);
    keepTemporary(f.root);
  });

  test("Overlapping registered directory and file targets are removed once without a pending failure", () => {
    const f = fixture("overlapping-registered-targets");
    const directory = "render-output/review";
    const frame = `${directory}/frame.jpg`;
    write(f.root, frame, "Disposable encoded review frame");
    registerTemporaryPaths(f.root, [directory, frame]);
    const result = cleanupCompletedProduction(f.root, production, {trackedFiles: []});
    assert.equal(result.status, "complete");
    assert.equal(existsSync(join(f.root, directory)), false);
    assert.deepEqual(result.errors, []);
    assert.equal(result.removed_paths.filter(path => path === directory).length, 1);
    assert.equal(result.removed_paths.includes(frame), false);
  });

  test("A production path cannot escape the workspace or select its root", () => {
    const f = fixture("path-boundary");
    assert.throws(() => cleanupCompletedProduction(f.root, "../outside", {trackedFiles: []}));
    assert.throws(() => cleanupCompletedProduction(f.root, ".", {trackedFiles: []}));
    keepTemporary(f.root);
  });

  test("Any tracked file in a deletion candidate aborts before deleting other candidates", () => {
    const f = fixture("tracked-file");
    const tracked = "work/runs/102/protected.txt";
    write(f.root, tracked, "Versioned and protected");
    assert.throws(() => cleanupCompletedProduction(f.root, production, {trackedFiles: [tracked]}));
    keepTemporary(f.root);
    assert.equal(readFileSync(join(f.root, tracked), "utf8"), "Versioned and protected");
  });

  test("A junction or symlink cannot make cleanup follow files outside its candidate", () => {
    const f = fixture("linked-descendant");
    const outside = join(f.root, "outside-candidate");
    write(f.root, "outside-candidate/keep.txt", "Must survive");
    symlinkSync(outside, join(f.root, "work/runs/102/linked-folder"), process.platform === "win32" ? "junction" : "dir");
    assert.throws(() => cleanupCompletedProduction(f.root, production, {trackedFiles: []}));
    keepTemporary(f.root);
    assert.equal(readFileSync(join(outside, "keep.txt"), "utf8"), "Must survive");
  });

  test("Verified completion removes this episode's run files and preserves source, records and unrelated work", () => {
    const f = fixture("complete");
    const result = cleanupCompletedProduction(f.root, production, {trackedFiles: []});
    assert.equal(result.status, "complete");
    assert.ok(result.reclaimed_bytes > 0);
    assert.equal(existsSync(join(f.root, "work/runs/101")), false);
    assert.equal(existsSync(join(f.root, "work/runs/102")), false);
    for (const path of ["work/runs/999/keep.txt", "work/python-deps/keep.txt", "work/unrelated.txt",
      "video/data/daily.json", `${production}/final-delivery.json`, `${production}/review.md`, "scripts/permanent-test.ts"])
      assert.equal(existsSync(join(f.root, path)), true, `Preserve ${path}`);
    const again = cleanupCompletedProduction(f.root, production, {trackedFiles: []});
    assert.equal(again.status, "complete");
    assert.equal(again.reclaimed_bytes, 0);
    assert.equal(again.removed_paths.length, 0);
  });

  console.log(`Production cleanup: ${passed} deletion-boundary regressions passed.`);
} finally {
  const allowedPrefix = join(checkout, "work", "cleanup-test-");
  if (!suiteRoot.startsWith(allowedPrefix) || suiteRoot === checkout)
    throw new Error("Refusing to remove a fixture outside its allocated directory");
  rmSync(suiteRoot, {recursive: true, force: true});
}
