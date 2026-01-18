"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DmgTarget = void 0;
exports.getDmgTemplatePath = getDmgTemplatePath;
exports.getDmgVendorPath = getDmgVendorPath;
exports.attachAndExecute = attachAndExecute;
exports.detach = detach;
exports.computeBackground = computeBackground;
exports.serializeString = serializeString;
exports.customizeDmg = customizeDmg;
exports.transformBackgroundFileIfNeed = transformBackgroundFileIfNeed;
exports.getImageSizeUsingSips = getImageSizeUsingSips;
const builder_util_1 = require("builder-util");
const path = require("path");
const hdiuil_1 = require("./hdiuil");
const fs_extra_1 = require("fs-extra");
var dmg_1 = require("./dmg");
Object.defineProperty(exports, "DmgTarget", { enumerable: true, get: function () { return dmg_1.DmgTarget; } });
const root = path.join(__dirname, "..");
function getDmgTemplatePath() {
    return path.join(root, "templates");
}
function getDmgVendorPath() {
    return path.join(root, "vendor");
}
async function attachAndExecute(dmgPath, readWrite, task) {
    //noinspection SpellCheckingInspection
    const args = ["attach", "-noverify", "-noautoopen"];
    if (readWrite) {
        args.push("-readwrite");
    }
    args.push(dmgPath);
    const attachResult = await (0, hdiuil_1.hdiUtil)(args);
    const deviceResult = attachResult == null ? null : /^(\/dev\/\w+)/.exec(attachResult);
    const device = deviceResult == null || deviceResult.length !== 2 ? null : deviceResult[1];
    if (device == null) {
        throw new Error(`Cannot mount: ${attachResult}`);
    }
    const volumePath = await findMountPath(path.basename(device));
    if (volumePath == null) {
        throw new Error(`Cannot find volume mount path for device: ${device}`);
    }
    return await (0, builder_util_1.executeFinally)(task(volumePath), () => detach(device));
}
/**
 * Find the mount path for a specific device from `hdiutil info`.
 */
async function findMountPath(devName, index = 1) {
    const info = await (0, hdiuil_1.hdiUtil)(["info"]);
    const lines = info.split("\n");
    const regex = new RegExp(`^/dev/${devName}(s\\d+)?\\s+\\S+\\s+(/Volumes/.+)$`);
    const matches = [];
    for (const line of lines) {
        const result = regex.exec(line);
        if (result && result.length >= 3) {
            matches.push(result[2]);
        }
    }
    return matches.length >= index ? matches[index - 1] : null;
}
async function detach(name) {
    return (0, hdiuil_1.hdiUtil)(["detach", "-quiet", name]).catch(async (e) => {
        if (hdiuil_1.hdiutilTransientExitCodes.has(e.code)) {
            // Delay then force unmount with verbose output
            await new Promise(resolve => setTimeout(resolve, 3000));
            return (0, hdiuil_1.hdiUtil)(["detach", "-force", name]);
        }
        throw e;
    });
}
async function computeBackground(packager) {
    const resourceList = await packager.resourceList;
    if (resourceList.includes("background.tiff")) {
        return path.join(packager.buildResourcesDir, "background.tiff");
    }
    else if (resourceList.includes("background.png")) {
        return path.join(packager.buildResourcesDir, "background.png");
    }
    else {
        return path.join(getDmgTemplatePath(), "background.tiff");
    }
}
/** @internal */
function serializeString(data) {
    return ('  $"' +
        data
            .match(/.{1,32}/g)
            .map(it => it.match(/.{1,4}/g).join(" "))
            .join('"\n  $"') +
        '"');
}
async function customizeDmg({ appPath, artifactPath, volumeName, specification, packager }) {
    var _a, _b, _c, _d, _e;
    const isValidIconTextSize = !!specification.iconTextSize && specification.iconTextSize >= 10 && specification.iconTextSize <= 16;
    const iconTextSize = isValidIconTextSize ? specification.iconTextSize : 12;
    const volumePath = path.join("/Volumes", volumeName);
    // https://github.com/electron-userland/electron-builder/issues/2115
    const backgroundFile = specification.background == null ? null : await transformBackgroundFileIfNeed(specification.background, packager.info.tempDirManager);
    const settings = {
        title: path.basename(volumePath),
        icon: await packager.getResource(specification.icon),
        "icon-size": specification.iconSize,
        "text-size": iconTextSize,
        "compression-level": Number(process.env.ELECTRON_BUILDER_COMPRESSION_LEVEL || "9"),
        // filesystem: specification.filesystem || "HFS+",
        format: specification.format,
        contents: ((_a = specification.contents) === null || _a === void 0 ? void 0 : _a.map(c => ({
            path: c.path || appPath, // path is required, when ommitted, appPath is used (backward compatibility
            x: c.x,
            y: c.y,
            name: c.name,
            type: c.type === "dir" ? "file" : c.type, // appdmg expects "file" for directories
            // hide_extension: c.hideExtension,
        }))) || [],
    };
    if (specification.backgroundColor != null || specification.background == null) {
        settings["background-color"] = specification.backgroundColor || "#ffffff";
        const window = specification.window;
        if (window != null) {
            settings.window = {
                position: {
                    x: (_b = window.x) !== null && _b !== void 0 ? _b : 100,
                    y: (_c = window.y) !== null && _c !== void 0 ? _c : 400,
                },
                size: {
                    width: (_d = window.width) !== null && _d !== void 0 ? _d : 540,
                    height: (_e = window.height) !== null && _e !== void 0 ? _e : 300,
                },
            };
        }
    }
    else {
        settings.background = backgroundFile;
        delete settings["background-color"];
    }
    if (!(0, builder_util_1.isEmptyOrSpaces)(settings.background)) {
        const size = await getImageSizeUsingSips(settings.background);
        settings.window = { position: { x: 400, y: Math.round((1440 - size.height) / 2) }, size, ...settings.window };
    }
    const settingsFile = await packager.getTempFile(".json");
    await (0, fs_extra_1.writeFile)(settingsFile, JSON.stringify(settings, null, 2));
    const python3Check = () => (0, builder_util_1.exec)("command", ["-v", "python3"]);
    const pythonCheck = () => (0, builder_util_1.exec)("command", ["-v", "python"]);
    const pythonPath = process.env.PYTHON_PATH || (await python3Check().catch(pythonCheck)) || (await pythonCheck());
    if (pythonPath == null || (0, builder_util_1.isEmptyOrSpaces)(pythonPath.trim())) {
        throw new Error("Cannot find 'python' or 'python3' executable, please ensure Python is installed and available in PATH or set PYTHON_PATH environment variable");
    }
    const vendorDir = getDmgVendorPath();
    await (0, builder_util_1.exec)(pythonPath.trim(), [path.join(vendorDir, "run_dmgbuild.py"), "-s", settingsFile, path.basename(volumePath), artifactPath], {
        cwd: vendorDir,
        env: {
            ...process.env,
            PYTHONIOENCODING: "utf8",
        },
    });
    // effectiveOptionComputed, when present, is purely for verifying result during test execution
    return (packager.packagerOptions.effectiveOptionComputed == null ||
        (await attachAndExecute(artifactPath, false, async (volumePath) => {
            var _a;
            return !(await packager.packagerOptions.effectiveOptionComputed({
                volumePath,
                specification: {
                    ...specification,
                    // clean up `contents` for test snapshot verification since app path is absolute to a unique tmp dir
                    contents: (_a = specification.contents) === null || _a === void 0 ? void 0 : _a.map((c) => {
                        var _a;
                        return ({
                            ...c,
                            path: path.extname((_a = c.path) !== null && _a !== void 0 ? _a : "") === ".app" ? path.relative(packager.projectDir, c.path) : c.path,
                        });
                    }),
                },
                packager,
            }));
        })));
}
async function transformBackgroundFileIfNeed(file, tmpDir) {
    if (path.extname(file.toLowerCase()) === ".tiff") {
        return file;
    }
    const retinaFile = file.replace(/\.([a-z]+)$/, "@2x.$1");
    if (await (0, builder_util_1.exists)(retinaFile)) {
        const tiffFile = await tmpDir.getTempFile({ suffix: ".tiff" });
        await (0, builder_util_1.exec)("tiffutil", ["-cathidpicheck", file, retinaFile, "-out", tiffFile]);
        return tiffFile;
    }
    return file;
}
async function getImageSizeUsingSips(background) {
    const stdout = await (0, builder_util_1.exec)("sips", ["-g", "pixelHeight", "-g", "pixelWidth", background]);
    let width = 0;
    let height = 0;
    const re = /([a-zA-Z]+):\s*(\d+)/;
    const lines = stdout.split("\n");
    for (const line of lines) {
        const match = re.exec(line);
        if (!match) {
            continue;
        }
        const key = match[1];
        const value = parseInt(match[2], 10);
        if (isNaN(value)) {
            throw new Error(`Failed to parse number from line: "${line}"`);
        }
        if (key === "pixelWidth") {
            width = value;
        }
        else if (key === "pixelHeight") {
            height = value;
        }
    }
    return { width, height };
}
//# sourceMappingURL=dmgUtil.js.map