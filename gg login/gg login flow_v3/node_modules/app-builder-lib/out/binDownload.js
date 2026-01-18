"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.download = download;
exports.getBinFromCustomLoc = getBinFromCustomLoc;
exports.getBinFromUrl = getBinFromUrl;
exports.getBin = getBin;
const builder_util_1 = require("builder-util");
const filename_1 = require("builder-util/out/filename");
const path = require("path");
const versionToPromise = new Map();
function download(url, output, checksum) {
    const args = ["download", "--url", url, "--output", output];
    if (checksum != null) {
        args.push("--sha512", checksum);
    }
    return (0, builder_util_1.executeAppBuilder)(args);
}
function getBinFromCustomLoc(name, version, binariesLocUrl, checksum) {
    const dirName = `${name}-${version}`;
    return getBin(dirName, binariesLocUrl, checksum);
}
function getBinFromUrl(releaseName, filenameWithExt, checksum, githubOrgRepo = "electron-userland/electron-builder-binaries") {
    let url;
    if (process.env.ELECTRON_BUILDER_BINARIES_DOWNLOAD_OVERRIDE_URL) {
        url = process.env.ELECTRON_BUILDER_BINARIES_DOWNLOAD_OVERRIDE_URL + "/" + filenameWithExt;
    }
    else {
        const baseUrl = process.env.NPM_CONFIG_ELECTRON_BUILDER_BINARIES_MIRROR ||
            process.env.npm_config_electron_builder_binaries_mirror ||
            process.env.npm_package_config_electron_builder_binaries_mirror ||
            process.env.ELECTRON_BUILDER_BINARIES_MIRROR ||
            `https://github.com/${githubOrgRepo}/releases/download/`;
        const middleUrl = process.env.NPM_CONFIG_ELECTRON_BUILDER_BINARIES_CUSTOM_DIR ||
            process.env.npm_config_electron_builder_binaries_custom_dir ||
            process.env.npm_package_config_electron_builder_binaries_custom_dir ||
            process.env.ELECTRON_BUILDER_BINARIES_CUSTOM_DIR ||
            releaseName;
        url = `${baseUrl}${middleUrl}/${filenameWithExt}`;
    }
    const cacheKey = `${releaseName}-${path.basename(filenameWithExt, path.extname(filenameWithExt))}`;
    return getBin(cacheKey, url, checksum);
}
function getBin(cacheKey, url, checksum) {
    var _a;
    // Old cache is ignored if cache environment variable changes
    const cacheName = (0, filename_1.sanitizeFileName)(`${(_a = process.env.ELECTRON_BUILDER_CACHE) !== null && _a !== void 0 ? _a : ""}${cacheKey}`);
    let promise = versionToPromise.get(cacheName); // if rejected, we will try to download again
    if (promise != null) {
        return promise;
    }
    promise = doGetBin(cacheKey, url, checksum);
    versionToPromise.set(cacheName, promise);
    return promise;
}
function doGetBin(name, url, checksum) {
    const args = ["download-artifact", "--name", name];
    if (url != null) {
        args.push("--url", url);
    }
    if (checksum != null) {
        args.push("--sha512", checksum);
    }
    return (0, builder_util_1.executeAppBuilder)(args);
}
//# sourceMappingURL=binDownload.js.map