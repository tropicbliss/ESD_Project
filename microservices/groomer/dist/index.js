"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
var client_1 = require("@prisma/client");
var express_1 = __importDefault(require("express"));
var zod_1 = require("zod");
var app = (0, express_1.default)();
var prisma = new client_1.PrismaClient();
// const PORT = parseInt(process.env.PORT);
// middleware & static files
app.use(express_1.default.urlencoded({ extended: false }));
app.use(express_1.default.json());
app.post("/create", function (req, res) { return __awaiter(void 0, void 0, void 0, function () {
    var json, schema, parsed, err_1;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                json = req.body;
                _a.label = 1;
            case 1:
                _a.trys.push([1, 3, , 4]);
                schema = zod_1.z.object({
                    name: zod_1.z.string(),
                    pictureUrl: zod_1.z.string().url(),
                    capacity: zod_1.z.number().min(1),
                    address: zod_1.z.string(),
                    contactNo: zod_1.z.string(),
                    email: zod_1.z.string().email(),
                    petType: zod_1.z.nativeEnum(client_1.PetType)
                });
                parsed = schema.parse(json);
                return [4 /*yield*/, prisma.groomer.create({
                        data: {
                            address: parsed.address,
                            capacity: parsed.capacity,
                            contactNo: parsed.contactNo,
                            email: parsed.email,
                            name: parsed.name,
                            pictureUrl: parsed.pictureUrl,
                            acceptedPets: {
                                create: {
                                    petType: parsed.petType
                                }
                            }
                        }
                    })];
            case 2:
                _a.sent();
                return [3 /*break*/, 4];
            case 3:
                err_1 = _a.sent();
                console.error(err_1);
                res.status(400);
                res.send({ message: "message is invalid" });
                return [2 /*return*/];
            case 4:
                res.status(200);
                res.send();
                return [2 /*return*/];
        }
    });
}); });
app.listen(5000, function () {
    console.log("Censorer listening on port ".concat(5000));
});
//# sourceMappingURL=index.js.map