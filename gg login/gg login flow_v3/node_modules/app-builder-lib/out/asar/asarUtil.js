"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AsarPackager = void 0;
const asar_1 = require("@electron/asar");
const builder_util_1 = require("builder-util");
const fs_1 = require("builder-util/out/fs");
const fs = require("fs-extra");
const fs_extra_1 = require("fs-extra");
const path = require("path");
const appFileCopier_1 = require("../util/appFileCopier");
const unpackDetector_1 = require("./unpackDetector");
const stream_1 = require("stream");
const os = require("os");
const resolvePath = async (file) => (file && (await (0, fs_1.exists)(file)) ? fs.realpath(file).catch(() => path.resolve(file)) : undefined);
const resolvePaths = async (filepaths) => {
    return Promise.all(filepaths.map(resolvePath)).then(paths => paths.filter((it) => it != null));
};
const DENYLIST = resolvePaths([
    "/usr",
    "/lib",
    "/bin",
    "/sbin",
    "/etc",
    "/tmp",
    "/var", // block whole /var by default. If $HOME is under /var, it's explicitly in ALLOWLIST - https://github.com/electron-userland/electron-builder/issues/9025#issuecomment-3575380041
    // macOS system directories
    "/System",
    "/Library",
    "/private",
    // Windows system directories
    process.env.SystemRoot,
    process.env.WINDIR,
]);
const ALLOWLIST = resolvePaths([
    os.tmpdir(), // always allow temp dir
    os.homedir(), // always allow home dir
]);
/** @internal */
class AsarPackager {
    constructor(packager, config) {
        this.packager = packager;
        this.config = config;
        this.outFile = path.join(config.resourcePath, `app.asar`);
    }
    async pack(fileSets) {
        const orderedFileSets = [
            // Write dependencies first to minimize offset changes to asar header
            ...fileSets.slice(1),
            // Finish with the app files that change most often
            fileSets[0],
        ].map(set => this.orderFileSet(set));
        const streams = await this.processFileSets(orderedFileSets);
        await this.executeElectronAsar(streams);
    }
    async executeElectronAsar(streams) {
        // override logger temporarily to clean up console (electron/asar does some internal logging that blogs up the default electron-builder logs)
        const consoleLogger = console.log;
        console.log = (...args) => {
            if (args[0] === "Ordering file has 100% coverage.") {
                return; // no need to log, this means our ordering logic is working correctly
            }
            builder_util_1.log.info({ args }, "logging @electron/asar");
        };
        await (0, asar_1.createPackageFromStreams)(this.outFile, streams);
        console.log = consoleLogger;
    }
    async processFileSets(fileSets) {
        var _a;
        const unpackedPaths = new Set();
        if (this.config.options.smartUnpack !== false) {
            for (const fileSet of fileSets) {
                (0, unpackDetector_1.detectUnpackedDirs)(fileSet, unpackedPaths);
            }
        }
        const results = [];
        const resultsPaths = new Set();
        for (const fileSet of fileSets) {
            // Don't use Promise.all, we need to retain order of execution/iteration through the already-ordered fileset
            for (const [index, file] of fileSet.files.entries()) {
                const transformedData = (_a = fileSet.transformedFiles) === null || _a === void 0 ? void 0 : _a.get(index);
                const stat = fileSet.metadata.get(file);
                const destination = path.relative(this.config.defaultDestination, (0, appFileCopier_1.getDestinationPath)(file, fileSet));
                const paths = Array.from(unpackedPaths).map(p => path.normalize(p));
                const isChildDirectory = (fileOrDirPath) => paths.includes(path.normalize(fileOrDirPath)) || paths.some(unpackedPath => path.normalize(fileOrDirPath).startsWith(unpackedPath + path.sep));
                const isUnpacked = (dir) => {
                    var _a, _b, _c;
                    const isChild = isChildDirectory(dir);
                    const isFileUnpacked = (_c = (_b = (_a = this.config).unpackPattern) === null || _b === void 0 ? void 0 : _b.call(_a, file, stat)) !== null && _c !== void 0 ? _c : false;
                    return isChild || isFileUnpacked;
                };
                this.processParentDirectories(isUnpacked, destination, results, resultsPaths);
                const result = await this.processFileOrSymlink({
                    file,
                    destination,
                    fileSet,
                    transformedData,
                    stat,
                    isUnpacked,
                });
                if (result != null) {
                    results.push(result);
                    resultsPaths.add(result.path);
                }
            }
        }
        return results;
    }
    processParentDirectories(isUnpacked, destination, results, resultsPaths) {
        // process parent directories
        let superDir = path.dirname(path.normalize(destination));
        while (superDir !== ".") {
            const dir = {
                type: "directory",
                path: superDir,
                unpacked: isUnpacked(superDir),
            };
            // add to results if not already present
            if (!resultsPaths.has(dir.path)) {
                results.push(dir);
                resultsPaths.add(dir.path);
            }
            superDir = path.dirname(superDir);
        }
    }
    async processFileOrSymlink(options) {
        const { isUnpacked, transformedData, file, destination, stat } = options;
        const unpacked = isUnpacked(destination);
        if (!stat.isFile() && !stat.isSymbolicLink()) {
            return { path: destination, unpacked, type: "directory" };
        }
        // write any data if provided, skip symlink check
        if (transformedData != null) {
            const streamGenerator = () => {
                return new stream_1.Readable({
                    read() {
                        this.push(transformedData);
                        this.push(null);
                    },
                });
            };
            const size = Buffer.byteLength(transformedData);
            return { path: destination, streamGenerator, unpacked, type: "file", stat: { mode: stat.mode, size } };
        }
        // verify that the file is not a direct link or symlinked to access/copy a system file
        await this.protectSystemAndUnsafePaths(file, await this.packager.info.getWorkspaceRoot());
        const config = {
            path: destination,
            streamGenerator: () => fs.createReadStream(file),
            unpacked,
            stat,
        };
        // file, stream directly
        if (!stat.isSymbolicLink()) {
            return {
                ...config,
                type: "file",
            };
        }
        // okay, it must be a symlink. evaluate link to be relative to source file in asar
        let link = await (0, fs_extra_1.readlink)(file);
        if (path.isAbsolute(link)) {
            link = path.relative(path.dirname(file), link);
        }
        return {
            ...config,
            type: "link",
            symlink: link,
        };
    }
    orderFileSet(fileSet) {
        const sortedFileEntries = Array.from(fileSet.files.entries());
        sortedFileEntries.sort(([, a], [, b]) => {
            if (a === b) {
                return 0;
            }
            // Place addons last because their signature changes per build
            const isAAddon = a.endsWith(".node");
            const isBAddon = b.endsWith(".node");
            if (isAAddon && !isBAddon) {
                return 1;
            }
            if (isBAddon && !isAAddon) {
                return -1;
            }
            // Otherwise order by name
            return a < b ? -1 : 1;
        });
        let transformedFiles;
        if (fileSet.transformedFiles) {
            transformedFiles = new Map();
            const indexMap = new Map();
            for (const [newIndex, [oldIndex]] of sortedFileEntries.entries()) {
                indexMap.set(oldIndex, newIndex);
            }
            for (const [oldIndex, value] of fileSet.transformedFiles) {
                const newIndex = indexMap.get(oldIndex);
                if (newIndex === undefined) {
                    const file = fileSet.files[oldIndex];
                    throw new Error(`Internal error: ${file} was lost while ordering asar`);
                }
                transformedFiles.set(newIndex, value);
            }
        }
        const { src, destination, metadata } = fileSet;
        return {
            src,
            destination,
            metadata,
            files: sortedFileEntries.map(([, file]) => file),
            transformedFiles,
        };
    }
    async checkAgainstRoots(target, allowRoots) {
        const resolved = await resolvePath(target);
        for (const root of allowRoots) {
            const resolvedRoot = root;
            if (resolved === resolvedRoot || (resolved === null || resolved === void 0 ? void 0 : resolved.startsWith(resolvedRoot + path.sep))) {
                return true;
            }
        }
        return false;
    }
    async protectSystemAndUnsafePaths(file, workspaceRoot) {
        const resolved = await resolvePath(file);
        const logFields = { source: file, realPath: resolved };
        const isUnsafe = async () => {
            const workspace = await resolvePath(workspaceRoot);
            if (workspace && (resolved === null || resolved === void 0 ? void 0 : resolved.startsWith(workspace))) {
                // if in workspace, always safe
                return false;
            }
            const allowed = await this.checkAgainstRoots(file, await ALLOWLIST);
            if (allowed) {
                return false; // allowlist is priority
            }
            const denied = await this.checkAgainstRoots(file, await DENYLIST);
            if (denied) {
                builder_util_1.log.error(logFields, `denied access to system or unsafe path`);
                return true;
            }
            // default
            builder_util_1.log.debug(logFields, `path is outside of explicit safe paths, defaulting to safe`);
            return false;
        };
        const unsafe = await isUnsafe();
        if (unsafe) {
            throw new Error(`Cannot copy file [${file}] symlinked to file [${resolved}] outside the package to a system or unsafe path`);
        }
    }
}
exports.AsarPackager = AsarPackager;
//# sourceMappingURL=asarUtil.js.map