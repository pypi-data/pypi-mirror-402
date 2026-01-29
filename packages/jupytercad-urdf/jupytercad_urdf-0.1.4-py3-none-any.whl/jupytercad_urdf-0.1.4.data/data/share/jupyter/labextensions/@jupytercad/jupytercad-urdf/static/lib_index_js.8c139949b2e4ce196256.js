"use strict";
(self["webpackChunk_jupytercad_jupytercad_urdf"] = self["webpackChunk_jupytercad_jupytercad_urdf"] || []).push([["lib_index_js"],{

/***/ "./lib/command.js":
/*!************************!*\
  !*** ./lib/command.js ***!
  \************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   CommandIDs: () => (/* binding */ CommandIDs),
/* harmony export */   addCommands: () => (/* binding */ addCommands)
/* harmony export */ });
/* harmony import */ var _jupytercad_base__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupytercad/base */ "webpack/sharing/consume/default/@jupytercad/base/@jupytercad/base");
/* harmony import */ var _jupytercad_base__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupytercad_base__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupytercad_schema__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupytercad/schema */ "webpack/sharing/consume/default/@jupytercad/schema/@jupytercad/schema");
/* harmony import */ var _jupytercad_schema__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupytercad_schema__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var uuid__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! uuid */ "webpack/sharing/consume/default/uuid/uuid?9e87");
/* harmony import */ var uuid__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(uuid__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _schema_json__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./schema.json */ "./lib/schema.json");
/* harmony import */ var _icon__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./icon */ "./lib/icon.js");






function newName(name, model) {
    const objectNames = model.getAllObject().map(obj => obj.name);
    if (!objectNames.includes(name)) {
        return name;
    }
    let index = 1;
    while (objectNames.includes(`${name} (${index})`)) {
        index++;
    }
    return `${name} (${index})`;
}
var CommandIDs;
(function (CommandIDs) {
    CommandIDs.exportUrdf = 'jupytercad:urdf:export';
})(CommandIDs || (CommandIDs = {}));
function addCommands(app, tracker, translator) {
    const trans = translator.load('jupyterlab');
    const { commands } = app;
    commands.addCommand(CommandIDs.exportUrdf, {
        label: trans.__('Export to URDF'),
        icon: _icon__WEBPACK_IMPORTED_MODULE_5__.exportIcon,
        isEnabled: () => Boolean(tracker.currentWidget),
        execute: Private.executeExportURDF(tracker)
    });
}
var Private;
(function (Private) {
    const urdfOperator = {
        title: 'Export to URDF',
        shape: 'Post::ExportURDF',
        default: (model) => {
            return {
                LinearDeflection: 0.01,
                AngularDeflection: 0.05
            };
        },
        syncData: (model) => {
            return (props) => {
                const { ...parameters } = props;
                const sharedModel = model.sharedModel;
                if (!sharedModel) {
                    return;
                }
                const objectsToExport = model
                    .getAllObject()
                    .filter(obj => obj.shape && !obj.shape.startsWith('Post::'));
                if (objectsToExport.length === 0) {
                    (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_2__.showErrorMessage)('No objects to export', 'The document has no geometric shapes to export.');
                    return;
                }
                const jobId = (0,uuid__WEBPACK_IMPORTED_MODULE_3__.v4)();
                const exportObjects = [];
                const filePath = model.filePath;
                const primitiveShapes = ['Part::Box', 'Part::Cylinder', 'Part::Sphere'];
                for (const object of objectsToExport) {
                    const isPrimitive = object.shape !== undefined &&
                        primitiveShapes.includes(object.shape);
                    const specificParams = {
                        isPrimitive,
                        // Pass primitive info only if it is one
                        ...(isPrimitive && {
                            shape: object.shape,
                            shapeParams: JSON.stringify(object.parameters)
                        })
                    };
                    const exportObjectName = newName(`${object.name}_STL_Export`, model);
                    const objectModel = {
                        shape: 'Post::ExportSTL',
                        parameters: {
                            ...parameters,
                            Object: object.name,
                            jobId,
                            totalFiles: objectsToExport.length,
                            filePath,
                            ...specificParams
                        },
                        visible: false,
                        name: exportObjectName,
                        shapeMetadata: {
                            shapeFormat: _jupytercad_schema__WEBPACK_IMPORTED_MODULE_1__.JCadWorkerSupportedFormat.STL,
                            workerId: 'jupytercad-urdf:worker'
                        }
                    };
                    exportObjects.push(objectModel);
                }
                sharedModel.transact(() => {
                    for (const obj of exportObjects) {
                        if (!sharedModel.objectExists(obj.name)) {
                            sharedModel.addObject(obj);
                        }
                    }
                });
            };
        }
    };
    function executeExportURDF(tracker) {
        return async (args) => {
            const current = tracker.currentWidget;
            if (!current) {
                return;
            }
            const dialog = new _jupytercad_base__WEBPACK_IMPORTED_MODULE_0__.FormDialog({
                model: current.model,
                title: urdfOperator.title,
                sourceData: urdfOperator.default(current.model),
                schema: _schema_json__WEBPACK_IMPORTED_MODULE_4__,
                syncData: urdfOperator.syncData(current.model),
                cancelButton: true
            });
            await dialog.launch();
        };
    }
    Private.executeExportURDF = executeExportURDF;
})(Private || (Private = {}));


/***/ }),

/***/ "./lib/icon.js":
/*!*********************!*\
  !*** ./lib/icon.js ***!
  \*********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   exportIcon: () => (/* binding */ exportIcon)
/* harmony export */ });
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _style_icon_export_urdf_plain_svg__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../style/icon/export-urdf-plain.svg */ "./style/icon/export-urdf-plain.svg");


const exportIcon = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'jupytercad:urdf-icon',
    svgstr: _style_icon_export_urdf_plain_svg__WEBPACK_IMPORTED_MODULE_1__
});


/***/ }),

/***/ "./lib/index.js":
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupytercad/schema */ "webpack/sharing/consume/default/@jupytercad/schema/@jupytercad/schema");
/* harmony import */ var _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_translation__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/translation */ "webpack/sharing/consume/default/@jupyterlab/translation");
/* harmony import */ var _jupyterlab_translation__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_translation__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _command__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./command */ "./lib/command.js");
/* harmony import */ var _schema_json__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./schema.json */ "./lib/schema.json");
/* harmony import */ var _worker__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./worker */ "./lib/worker.js");





/**
 * Initialization data for the jupytercad-urdf extension.
 */
const plugin = {
    id: 'jupytercad-urdf:plugin',
    description: 'A JupyterCAD URDF export extension.',
    autoStart: true,
    requires: [
        _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__.IJCadWorkerRegistryToken,
        _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__.IJCadFormSchemaRegistryToken,
        _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__.IJupyterCadDocTracker,
        _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__.IJCadExternalCommandRegistryToken
    ],
    optional: [_jupyterlab_translation__WEBPACK_IMPORTED_MODULE_1__.ITranslator],
    activate: (app, workerRegistry, schemaRegistry, tracker, externalCommandRegistry, translator) => {
        console.log('JupyterLab extension jupytercad-urdf is activated!');
        translator = translator !== null && translator !== void 0 ? translator : _jupyterlab_translation__WEBPACK_IMPORTED_MODULE_1__.nullTranslator;
        const WORKER_ID = 'jupytercad-urdf:worker';
        const contentsManager = app.serviceManager.contents;
        const worker = new _worker__WEBPACK_IMPORTED_MODULE_4__.URDFWorker({ tracker, contentsManager });
        workerRegistry.registerWorker(WORKER_ID, worker);
        schemaRegistry.registerSchema('Post::ExportURDF', _schema_json__WEBPACK_IMPORTED_MODULE_3__);
        (0,_command__WEBPACK_IMPORTED_MODULE_2__.addCommands)(app, tracker, translator);
        externalCommandRegistry.registerCommand({
            name: 'Export to URDF',
            id: _command__WEBPACK_IMPORTED_MODULE_2__.CommandIDs.exportUrdf
        });
    }
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (plugin);


/***/ }),

/***/ "./lib/schema.json":
/*!*************************!*\
  !*** ./lib/schema.json ***!
  \*************************/
/***/ ((module) => {

module.exports = /*#__PURE__*/JSON.parse('{"type":"object","properties":{"LinearDeflection":{"type":"number","description":"Linear deflection for all meshes (smaller = more triangles)","minimum":0.0001,"maximum":1,"default":0.01},"AngularDeflection":{"type":"number","description":"Angular deflection for all meshes (in radians)","minimum":0.01,"maximum":1,"default":0.05}},"required":[],"additionalProperties":false}');

/***/ }),

/***/ "./lib/urdf.js":
/*!*********************!*\
  !*** ./lib/urdf.js ***!
  \*********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   generateUrdf: () => (/* binding */ generateUrdf)
/* harmony export */ });
/**
 * Utility functions for generating URDF files.
 */
/**
 * Converts an axis-angle rotation to Roll, Pitch, Yaw Euler angles.
 * @param axis The rotation axis (3-element array).
 * @param angleInDegrees The rotation angle in degrees.
 * @returns An object with {r, p, y} values.
 */
function axisAngleToRpy(axis, angleInDegrees) {
    const angle = angleInDegrees * (Math.PI / 180);
    const [ax, ay, az] = axis;
    const s = Math.sin(angle / 2);
    const c = Math.cos(angle / 2);
    const qx = ax * s;
    const qy = ay * s;
    const qz = az * s;
    const qw = c;
    const sinp = 2 * (qw * qy - qz * qx);
    let r, p, y;
    // Check for gimbal lock
    if (Math.abs(sinp) >= 1) {
        p = (Math.PI / 2) * Math.sign(sinp);
        r = 2 * Math.atan2(qx, qw);
        y = 0;
    }
    else {
        p = Math.asin(sinp);
        const sinr_cosp = 2 * (qw * qx + qy * qz);
        const cosr_cosp = 1 - 2 * (qx * qx + qy * qy);
        r = Math.atan2(sinr_cosp, cosr_cosp);
        const siny_cosp = 2 * (qw * qz + qx * qy);
        const cosy_cosp = 1 - 2 * (qy * qy + qz * qz);
        y = Math.atan2(siny_cosp, cosy_cosp);
    }
    return { r, p, y };
}
/**
 * Generates the URDF XML string from primitives and meshes.
 */
function generateUrdf(primitives, meshes, robotName) {
    var _a, _b, _c;
    let links = '';
    let materials = '';
    // Map to store color to material mappings
    const materialMap = new Map();
    let materialIndex = 0;
    const getMaterialTags = (params) => {
        const color = params.Color;
        if (!color) {
            return { main: '', ref: '' };
        }
        if (materialMap.has(color)) {
            return { main: '', ref: `<material name="${materialMap.get(color)}"/>` };
        }
        const materialName = `mat_${materialIndex++}`;
        materialMap.set(color, materialName);
        // Basic hex to RGB conversion
        const r = parseInt(color.slice(1, 3), 16) / 255;
        const g = parseInt(color.slice(3, 5), 16) / 255;
        const b = parseInt(color.slice(5, 7), 16) / 255;
        const mainTag = `\n  <material name="${materialName}">\n    <color rgba="${r.toFixed(2)} ${g.toFixed(2)} ${b.toFixed(2)} 1.0"/>\n  </material>`;
        const refTag = `<material name="${materialName}"/>`;
        return { main: mainTag, ref: refTag };
    };
    // Generate links for primitive shapes
    for (const primitive of primitives) {
        const { name, shape, params } = primitive;
        const pos = ((_a = params.Placement) === null || _a === void 0 ? void 0 : _a.Position) || [0, 0, 0];
        const rotAxis = ((_b = params.Placement) === null || _b === void 0 ? void 0 : _b.Axis) || [0, 0, 1];
        const rotAngle = ((_c = params.Placement) === null || _c === void 0 ? void 0 : _c.Angle) || 0;
        const rpy = axisAngleToRpy(rotAxis, rotAngle);
        const originTag = `<origin xyz="${pos[0]} ${pos[1]} ${pos[2]}" rpy="${rpy.r} ${rpy.p} ${rpy.y}" />`;
        const materialTags = getMaterialTags(params);
        materials += materialTags.main;
        let geometryTag = '';
        switch (shape) {
            case 'Part::Box':
                geometryTag = `<box size="${params.Length} ${params.Width} ${params.Height}"/>`;
                break;
            case 'Part::Cylinder':
                geometryTag = `<cylinder radius="${params.Radius}" length="${params.Height}"/>`;
                break;
            case 'Part::Sphere':
                geometryTag = `<sphere radius="${params.Radius}"/>`;
                break;
        }
        if (geometryTag) {
            links += `
  <link name="${name}">
    <visual>
      <geometry>
      ${geometryTag}
      </geometry>
      ${originTag}
      ${materialTags.ref}
    </visual>
  </link>
  `;
        }
    }
    // Generate links for mesh shapes
    for (const file of meshes) {
        const linkName = file.name.replace('.stl', '');
        const materialTags = getMaterialTags(file.params);
        materials += materialTags.main;
        links += `
  <link name="${linkName}">
    <visual>
      <geometry>
        <mesh filename="package://meshes/${file.name}" />
      </geometry>
      ${materialTags.ref}
    </visual>
  </link>
  `;
    }
    return `<robot name="${robotName}">${materials}${links}\n</robot>`;
}


/***/ }),

/***/ "./lib/worker.js":
/*!***********************!*\
  !*** ./lib/worker.js ***!
  \***********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   URDFWorker: () => (/* binding */ URDFWorker)
/* harmony export */ });
/* harmony import */ var _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupytercad/schema */ "webpack/sharing/consume/default/@jupytercad/schema/@jupytercad/schema");
/* harmony import */ var _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _lumino_coreutils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @lumino/coreutils */ "webpack/sharing/consume/default/@lumino/coreutils");
/* harmony import */ var _lumino_coreutils__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_lumino_coreutils__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var uuid__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! uuid */ "webpack/sharing/consume/default/uuid/uuid?9e87");
/* harmony import */ var uuid__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(uuid__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _urdf__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./urdf */ "./lib/urdf.js");





class URDFWorker {
    constructor(options) {
        this.shapeFormat = _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__.JCadWorkerSupportedFormat.STL;
        this._jobs = new Map();
        this._ready = new _lumino_coreutils__WEBPACK_IMPORTED_MODULE_2__.PromiseDelegate();
        this._tracker = options.tracker;
        this._contentsManager = options.contentsManager;
    }
    get ready() {
        this._ready.resolve();
        return this._ready.promise;
    }
    register(options) {
        const id = (0,uuid__WEBPACK_IMPORTED_MODULE_3__.v4)();
        return id;
    }
    unregister(id) {
        // empty
    }
    postMessage(msg) {
        if (msg.action !== _jupytercad_schema__WEBPACK_IMPORTED_MODULE_0__.WorkerAction.POSTPROCESS) {
            return;
        }
        const payload = msg.payload;
        if (!payload || !payload.jcObject || payload.postShape === undefined) {
            return;
        }
        const { jcObject, postShape } = payload;
        const { jobId, totalFiles, Object: objectName, isPrimitive, shape, shapeParams, filePath } = jcObject.parameters;
        if (!jobId || !filePath) {
            return;
        }
        if (!this._jobs.has(jobId)) {
            this._jobs.set(jobId, {
                primitives: [],
                meshes: [],
                total: totalFiles,
                received: 0,
                jcObjects: [],
                filePath: filePath
            });
        }
        const job = this._jobs.get(jobId);
        job.received++;
        job.jcObjects.push(jcObject.name);
        if (isPrimitive) {
            job.primitives.push({
                name: objectName,
                shape: shape,
                params: JSON.parse(shapeParams)
            });
        }
        else {
            job.meshes.push({
                name: `${objectName}.stl`,
                content: postShape,
                params: jcObject.parameters
            });
        }
        if (job.received === job.total) {
            this._packageAndSave(job);
            this._cleanup(job.jcObjects);
            this._jobs.delete(jobId);
        }
    }
    async _packageAndSave(job) {
        const { primitives, meshes, filePath } = job;
        const contentsManager = this._contentsManager;
        if (!contentsManager) {
            console.error('FATAL: [worker.ts] ContentsManager was not provided to the worker.');
            (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.showErrorMessage)('URDF Export Failed', 'ContentsManager not available in worker.');
            return;
        }
        const pathParts = filePath.split('/');
        const docName = pathParts.pop() || 'untitled.jcad';
        const baseName = docName.substring(0, docName.lastIndexOf('.'));
        const dirPath = pathParts.join('/');
        const exportDirName = baseName;
        const exportDirPath = dirPath
            ? `${dirPath}/${exportDirName}`
            : exportDirName;
        const urdfFileName = `${baseName}.urdf`;
        const urdfPath = `${exportDirPath}/${urdfFileName}`;
        const meshesDirPath = `${exportDirPath}/meshes`;
        try {
            // Create main export directory if it doesn't exist
            try {
                await contentsManager.get(exportDirPath);
            }
            catch (_a) {
                await contentsManager
                    .newUntitled({ path: dirPath, type: 'directory' })
                    .then((model) => contentsManager.rename(model.path, exportDirPath));
            }
            // Create meshes directory if needed and it doesn't exist
            if (meshes.length > 0) {
                try {
                    await contentsManager.get(meshesDirPath);
                }
                catch (_b) {
                    await contentsManager
                        .newUntitled({ path: exportDirPath, type: 'directory' })
                        .then((model) => contentsManager.rename(model.path, meshesDirPath));
                }
            }
            // Save or overwrite the URDF file
            const urdfContent = (0,_urdf__WEBPACK_IMPORTED_MODULE_4__.generateUrdf)(primitives, meshes, baseName);
            await contentsManager.save(urdfPath, {
                type: 'file',
                format: 'text',
                content: urdfContent
            });
            // Save or overwrite mesh files
            for (const file of meshes) {
                const stlPath = `${meshesDirPath}/${file.name}`;
                await contentsManager.save(stlPath, {
                    type: 'file',
                    format: 'text',
                    content: file.content
                });
            }
            (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.showDialog)({
                title: 'Export Successful',
                body: `URDF robot exported successfully to ${exportDirPath}`,
                buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.Dialog.okButton()]
            });
        }
        catch (error) {
            console.error('ERROR: [worker.ts] Failed during file save operation:', error);
            (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.showErrorMessage)('URDF Export Failed', error);
        }
    }
    _cleanup(objectNames) {
        const currentWidget = this._tracker.currentWidget;
        if (!currentWidget) {
            return;
        }
        const sharedModel = currentWidget.model.sharedModel;
        if (sharedModel) {
            sharedModel.transact(() => {
                for (const name of objectNames) {
                    if (sharedModel.objectExists(name)) {
                        sharedModel.removeObjectByName(name);
                    }
                }
            });
        }
    }
}


/***/ }),

/***/ "./style/icon/export-urdf-plain.svg":
/*!******************************************!*\
  !*** ./style/icon/export-urdf-plain.svg ***!
  \******************************************/
/***/ ((module) => {

module.exports = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<!-- Created with Inkscape (http://www.inkscape.org/) -->\n\n<svg\n   width=\"297mm\"\n   height=\"297mm\"\n   viewBox=\"0 0 297 297\"\n   version=\"1.1\"\n   xmlns=\"http://www.w3.org/2000/svg\"\n   xmlns:svg=\"http://www.w3.org/2000/svg\">\n  <g\n       class=\"jp-icon3\"\n       fill=\"#616161\">\n      <path\n         d=\"m 178.1328,187.99525 c -28.93792,1e-5 -53.63752,16.84236 -58.4078,39.82754 h -10.25762 a 4.701161,4.701161 135 0 0 -4.70116,4.70116 v 52.55825 a 5.6272026,5.6272026 45 0 0 5.6272,5.6272 h 135.48031 a 5.6272026,5.6272026 135 0 0 5.6272,-5.6272 v -52.55825 a 4.701161,4.701161 45 0 0 -4.70116,-4.70116 l -10.25916,0 c -4.77028,-22.98518 -29.46989,-39.82753 -58.40781,-39.82754 z\" />\n      <path\n         d=\"m 143.2817,15.095203 a 17.199638,17.199638 0 0 0 -2.34405,0.250631 17.199638,17.199638 0 0 0 -8.39483,4.046781 L 79.878847,65.943264 a 17.197918,17.197918 0 0 0 -2.733683,3.073197 L 55.828118,65.492128 a 10.584392,10.584392 0 0 0 -9.20874,2.958993 L 22.672002,92.398497 a 10.583334,10.583334 0 0 0 0,14.966533 10.583334,10.583334 0 0 0 14.966529,0 L 57.742214,87.263927 78.878908,90.75622 a 17.197918,17.197918 0 0 0 0,5.17e-4 17.197918,17.197918 0 0 0 0.518315,0.515731 h 5.17e-4 l 3.494877,21.141342 -20.101616,20.10369 a 10.583334,10.583334 0 0 0 0,14.96704 10.583334,10.583334 0 0 0 14.967046,0 l 23.946863,-23.94737 a 10.584392,10.584392 0 0 0 2.95744,-9.20926 l -3.53777,-21.405414 a 17.197918,17.197918 0 0 0 1.53376,-1.207678 l 38.76559,-34.26561 43.55858,57.496232 -23.6585,109.2383 a 17.197918,17.197918 0 0 0 13.16819,20.44733 17.197918,17.197918 0 0 0 20.44939,-13.16819 l 25.33179,-116.96289 a 17.199638,17.199638 0 0 0 -3.09955,-14.0255 L 157.64258,21.894788 A 17.199638,17.199638 0 0 0 143.2817,15.095203 Z m 0.61753,4.748548 a 13.758333,13.361459 0 0 1 13.79244,13.317533 v 0.04393 A 13.758333,13.361459 0 0 1 143.94471,46.566668 13.758333,13.361459 0 0 1 130.175,33.22743 13.758333,13.361459 0 0 1 143.89923,19.843751 Z m 59.00209,78.052085 a 13.758333,13.361459 0 0 1 13.79244,13.317534 v 0.0439 a 13.758333,13.361459 0 0 1 -13.74697,13.36146 13.758333,13.361459 0 0 1 -13.7697,-13.33923 13.758333,13.361459 0 0 1 13.72423,-13.383684 z\" />\n      <path\n         d=\"m 203.3075,84.232416 a 26.584653,26.584656 0 0 0 -26.58466,26.584654 26.584653,26.584656 0 0 0 26.58466,26.58466 26.584653,26.584656 0 0 0 26.58465,-26.58466 26.584653,26.584656 0 0 0 -26.58465,-26.584654 z m 0,14.953864 a 11.630786,11.630786 0 0 1 11.63078,11.63079 11.630786,11.630786 0 0 1 -11.63078,11.63079 11.630786,11.630786 0 0 1 -11.63079,-11.63079 11.630786,11.630786 0 0 1 11.63079,-11.63079 z\" />\n      <path\n         d=\"M 144.08958,6.2906711 A 26.584653,26.584656 0 0 0 117.50492,32.875323 26.584653,26.584656 0 0 0 144.08958,59.459981 26.584653,26.584656 0 0 0 170.67423,32.875323 26.584653,26.584656 0 0 0 144.08958,6.2906711 Z m 0,14.9538619 a 11.630786,11.630786 0 0 1 11.63078,11.63079 11.630786,11.630786 0 0 1 -11.63078,11.63079 11.630786,11.630786 0 0 1 -11.63079,-11.63079 11.630786,11.630786 0 0 1 11.63079,-11.63079 z\" />\n  </g>\n</svg>\n";

/***/ })

}]);
//# sourceMappingURL=lib_index_js.8c139949b2e4ce196256.js.map