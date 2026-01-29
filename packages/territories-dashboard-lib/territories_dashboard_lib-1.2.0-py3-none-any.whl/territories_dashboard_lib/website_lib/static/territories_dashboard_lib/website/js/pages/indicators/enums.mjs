const THOUSANDS = "k";
const MILLIONS = "M";

const MeshLevel = {
    fr: "fr",
    reg: "reg",
    dep: "dep",
    epci: "epci",
    com: "com",
    aom: "aom",
};

const COLORS = {
    "#6A6AF4": "white",
    "#000091": "white",
    "#E1000F": "white",
    "#B7A73F": "black",
    "#66673D": "white",
    "#68A532": "black",
    "#447049": "white",
    "#00A95F": "black",
    "#297254": "white",
    "#009081": "black",
    "#37635F": "white",
    "#009099": "black",
    "#006A6F": "white",
    "#465F9D": "white",
    "#2F4077": "white",
    "#417DC4": "black",
    "#3558A2": "white",
    "#A558A0": "black",
    "#6E445A": "white",
    "#E18B76": "black",
    "#8D533E": "white",
    "#CE614A": "black",
    "#A94645": "white",
    "#C8AA39": "black",
    "#716043": "white",
    "#C3992A": "black",
    "#695240": "white",
    "#E4794A": "black",
    "#755348": "white",
    "#D1B781": "black",
    "#685C48": "white",
    "#C08C65": "black",
    "#845d48": "white",
    "#BD987A": "black",
    "#745B47": "white",
    "#AEA397": "black",
    "#6A6156": "white",
    "#C9191E": "white",
};

const PATTERNS = [
    "plus",
    "square",
    "zigzag",
    "dash",
    "dot",
    "cross",
    "weave",
    "triangle",
    "disc",
    "box",
    "ring",
    "line",
    "diagonal",
    "cross-dash",
    "dot-dash",
    "triangle-inverted",
    "diamond",
    "line-vertical",
    "zigzag-vertical",
    "diagonal-right-left",
    "diamond-box",
];

function getMeshLevelTitle(meshLevel) {
    switch (meshLevel) {
        case MeshLevel.reg:
            return "Région";
        case MeshLevel.dep:
            return "Département";
        case MeshLevel.epci:
            return "Intercommunalité";
        case MeshLevel.com:
            return "Commune";
        case MeshLevel.fr:
            return "France entière";
        case MeshLevel.aom:
            return "AOM";
    }
}

const MAX_TERRITORIES_BEFORE_HIDE = 5;
const SHORT_MESH_NUMBER_OF_LETTERS = 3;

export {
    MILLIONS,
    THOUSANDS,
    COLORS,
    MeshLevel,
    getMeshLevelTitle,
    MAX_TERRITORIES_BEFORE_HIDE,
    SHORT_MESH_NUMBER_OF_LETTERS,
    PATTERNS,
};
