"""Python translation of MARC::Lint::CodeData tables

This module exposes the same hash-style lookups as the Perl
`MARC::Lint::CodeData` package, but using plain Python dicts.

Only the data actually used by `MARC::Lint` itself is needed here
for understanding how language, geographic area, and country codes
are validated.

Original MARC::Lint Perl module:
    Copyright (C) 2001-2011 Bryan Baldus, Ed Summers, and Dan Lester
    Available under the Perl License (Artistic + GPL)
    https://metacpan.org/dist/MARC-Lint

Python port:
    Copyright (C) 2025 Jacob Collins
"""

# Required fields for minimal valid bibliographic record
REQUIRED_FIELDS = {"001", "008", "245"}

# Control fields (00X)
CONTROL_FIELDS = {"001", "003", "005", "006", "007", "008"}

# ============================================================================
# LEADER VALIDATION CODES
# ============================================================================

# Leader/05 - Record Status
LEADER_RECORD_STATUS: dict[str, str] = {
    "a": "Increase in encoding level",
    "c": "Corrected or revised",
    "d": "Deleted",
    "n": "New",
    "p": "Increase in encoding level from prepublication",
}
"""Valid values for Leader position 05 (Record Status)."""

# Leader/06 - Type of Record
LEADER_TYPE_OF_RECORD: dict[str, str] = {
    "a": "Language material",
    "c": "Notated music",
    "d": "Manuscript notated music",
    "e": "Cartographic material",
    "f": "Manuscript cartographic material",
    "g": "Projected medium",
    "i": "Nonmusical sound recording",
    "j": "Musical sound recording",
    "k": "Two-dimensional nonprojectable graphic",
    "m": "Computer file",
    "o": "Kit",
    "p": "Mixed materials",
    "r": "Three-dimensional artifact or naturally occurring object",
    "t": "Manuscript language material",
}
"""Valid values for Leader position 06 (Type of Record)."""

# Leader/07 - Bibliographic Level
LEADER_BIBLIOGRAPHIC_LEVEL: dict[str, str] = {
    "a": "Monographic component part",
    "b": "Serial component part",
    "c": "Collection",
    "d": "Subunit",
    "i": "Integrating resource",
    "m": "Monograph/Item",
    "s": "Serial",
}
"""Valid values for Leader position 07 (Bibliographic Level)."""

# Leader/08 - Type of Control
LEADER_TYPE_OF_CONTROL: dict[str, str] = {
    " ": "No specified type",
    "a": "Archival",
}
"""Valid values for Leader position 08 (Type of Control)."""

# Leader/09 - Character Coding Scheme
LEADER_CHARACTER_CODING_SCHEME: dict[str, str] = {
    " ": "MARC-8",
    "a": "UCS/Unicode",
}
"""Valid values for Leader position 09 (Character Coding Scheme)."""

# Leader/17 - Encoding Level
LEADER_ENCODING_LEVEL: dict[str, str] = {
    " ": "Full level",
    "1": "Full level, material not examined",
    "2": "Less-than-full level, material not examined",
    "3": "Abbreviated level",
    "4": "Core level",
    "5": "Partial (preliminary) level",
    "7": "Minimal level",
    "8": "Prepublication level",
    "u": "Unknown",
    "z": "Not applicable",
}
"""Valid values for Leader position 17 (Encoding Level)."""

# Leader/18 - Descriptive Cataloging Form
LEADER_DESCRIPTIVE_CATALOGING_FORM: dict[str, str] = {
    " ": "Non-ISBD",
    "a": "AACR 2",
    "c": "ISBD punctuation omitted",
    "i": "ISBD punctuation included",
    "n": "Non-ISBD punctuation omitted",
    "u": "Unknown",
}
"""Valid values for Leader position 18 (Descriptive Cataloging Form)."""

# Leader/19 - Multipart Resource Record Level
LEADER_MULTIPART_RESOURCE_RECORD_LEVEL: dict[str, str] = {
    " ": "Not specified or not applicable",
    "a": "Set",
    "b": "Part with independent title",
    "c": "Part with dependent title",
}
"""Valid values for Leader position 19 (Multipart Resource Record Level)."""

# ============================================================================
# 008 CONTROL FIELD VALIDATION
# ============================================================================

# 008/06 - Type of Date/Publication Status
TYPE_OF_DATE: dict[str, str] = {
    "b": "No dates given; B.C. date involved",
    "c": "Continuing resource currently published",
    "d": "Continuing resource ceased publication",
    "e": "Detailed date",
    "i": "Inclusive dates of collection",
    "k": "Range of years of bulk of collection",
    "m": "Multiple dates",
    "n": "Dates unknown",
    "p": "Date of distribution/release/issue and production/recording session when different",
    "q": "Questionable date",
    "r": "Reprint/reissue date and original date",
    "s": "Single known date/probable date",
    "t": "Publication date and copyright date",
    "u": "Continuing resource status unknown",
    "|": "No attempt to code",
}
"""Valid values for 008/06 (Type of Date/Publication Status)."""

# 008/35-37 - Language (uses LANGUAGE_CODES dict)

GEOG_AREA_CODES_STR: str = (
    "a------\ta-af---\ta-ai---\ta-aj---\ta-ba---\ta-bg---\ta-bn---\ta-br---\t"
    "a-bt---\ta-bx---\ta-cb---\ta-cc---\ta-cc-an\ta-cc-ch\ta-cc-cq\ta-cc-fu\t"
    "a-cc-ha\ta-cc-he\ta-cc-hh\ta-cc-hk\ta-cc-ho\ta-cc-hp\ta-cc-hu\ta-cc-im\t"
    "a-cc-ka\ta-cc-kc\ta-cc-ki\ta-cc-kn\ta-cc-kr\ta-cc-ku\ta-cc-kw\ta-cc-lp\t"
    "a-cc-mh\ta-cc-nn\ta-cc-pe\ta-cc-sh\ta-cc-sm\ta-cc-sp\ta-cc-ss\ta-cc-su\t"
    "a-cc-sz\ta-cc-ti\ta-cc-tn\ta-cc-ts\ta-cc-yu\ta-ccg--\ta-cck--\ta-ccp--\t"
    "a-ccs--\ta-ccy--\ta-ce---\ta-ch---\ta-cy---\ta-em---\ta-gs---\ta-ii---\t"
    "a-io---\ta-iq---\ta-ir---\ta-is---\ta-ja---\ta-jo---\ta-kg---\ta-kn---\t"
    "a-ko---\ta-kr---\ta-ku---\ta-kz---\ta-le---\ta-ls---\ta-mk---\ta-mp---\t"
    "a-my---\ta-np---\ta-nw---\ta-ph---\ta-pk---\ta-pp---\ta-qa---\ta-si---\t"
    "a-su---\ta-sy---\ta-ta---\ta-th---\ta-tk---\ta-ts---\ta-tu---\ta-uz---\t"
    "a-vt---\ta-ye---\taa-----\tab-----\tac-----\tae-----\taf-----\tag-----\t"
    "ah-----\tai-----\tak-----\tam-----\tan-----\tao-----\taopf---\taoxp---\t"
    "ap-----\tar-----\tas-----\tat-----\tau-----\taw-----\tawba---\tawgz---\t"
    "ay-----\taz-----\tb------\tc------\tcc-----\tcl-----\td------\tdd-----\t"
    "e------\te-aa---\te-an---\te-au---\te-be---\te-bn---\te-bu---\te-bw---\t"
    "e-ci---\te-cs---\te-dk---\te-er---\te-fi---\te-fr---\te-ge---\te-gi---\t"
    "e-gr---\te-gw---\te-gx---\te-hu---\te-ic---\te-ie---\te-it---\te-kv---\t"
    "e-lh---\te-li---\te-lu---\te-lv---\te-mc---\te-mm---\te-mo---\te-mv---\t"
    "e-ne---\te-no---\te-pl---\te-po---\te-rb---\te-rm---\te-ru---\te-sm---\t"
    "e-sp---\te-sw---\te-sz---\te-uk---\te-uk-en\te-uk-ni\te-uk-st\te-uk-ui\t"
    "e-uk-wl\te-un---\te-ur---\te-urc--\te-ure--\te-urf--\te-urk--\te-urn--\t"
    "e-urp--\te-urr--\te-urs--\te-uru--\te-urw--\te-vc---\te-xn---\te-xo---\t"
    "e-xr---\te-xv---\te-yu---\tea-----\teb-----\tec-----\ted-----\tee-----\t"
    "el-----\ten-----\teo-----\tep-----\ter-----\tes-----\tev-----\tew-----\t"
    "f------\tf-ae---\tf-ao---\tf-bd---\tf-bs---\tf-cd---\tf-cf---\tf-cg---\t"
    "f-cm---\tf-cx---\tf-dm---\tf-ea---\tf-eg---\tf-et---\tf-ft---\tf-gh---\t"
    "f-gm---\tf-go---\tf-gv---\tf-iv---\tf-ke---\tf-lb---\tf-lo---\tf-ly---\t"
    "f-mg---\tf-ml---\tf-mr---\tf-mu---\tf-mw---\tf-mz---\tf-ng---\tf-nr---\t"
    "f-pg---\tf-rh---\tf-rw---\tf-sa---\tf-sd---\tf-sf---\tf-sg---\tf-sh---\t"
    "f-sj---\tf-sl---\tf-so---\tf-sq---\tf-ss---\tf-sx---\tf-tg---\tf-ti---\t"
    "f-tz---\tf-ua---\tf-ug---\tf-uv---\tf-za---\tfa-----\tfb-----\tfc-----\t"
    "fd-----\tfe-----\tff-----\tfg-----\tfh-----\tfi-----\tfl-----\tfn-----\t"
    "fq-----\tfr-----\tfs-----\tfu-----\tfv-----\tfw-----\tfz-----\th------\t"
    "i------\ti-bi---\ti-cq---\ti-fs---\ti-hm---\ti-mf---\ti-my---\ti-re---\t"
    "i-se---\ti-xa---\ti-xb---\ti-xc---\ti-xo---\tl------\tln-----\tlnaz---\t"
    "lnbm---\tlnca---\tlncv---\tlnfa---\tlnjn---\tlnma---\tlnsb---\tls-----\t"
    "lsai---\tlsbv---\tlsfk---\tlstd---\tlsxj---\tlsxs---\tm------\tma-----\t"
    "mb-----\tme-----\tmm-----\tmr-----\tn------\tn-cn---\tn-cn-ab\tn-cn-bc\t"
    "n-cn-mb\tn-cn-nf\tn-cn-nk\tn-cn-ns\tn-cn-nt\tn-cn-nu\tn-cn-on\tn-cn-pi\t"
    "n-cn-qu\tn-cn-sn\tn-cn-yk\tn-cnh--\tn-cnm--\tn-cnp--\tn-gl---\tn-mx---\t"
    "n-us---\tn-us-ak\tn-us-al\tn-us-ar\tn-us-az\tn-us-ca\tn-us-co\tn-us-ct\t"
    "n-us-dc\tn-us-de\tn-us-fl\tn-us-ga\tn-us-hi\tn-us-ia\tn-us-id\tn-us-il\t"
    "n-us-in\tn-us-ks\tn-us-ky\tn-us-la\tn-us-ma\tn-us-md\tn-us-me\tn-us-mi\t"
    "n-us-mn\tn-us-mo\tn-us-ms\tn-us-mt\tn-us-nb\tn-us-nc\tn-us-nd\tn-us-nh\t"
    "n-us-nj\tn-us-nm\tn-us-nv\tn-us-ny\tn-us-oh\tn-us-ok\tn-us-or\tn-us-pa\t"
    "n-us-ri\tn-us-sc\tn-us-sd\tn-us-tn\tn-us-tx\tn-us-ut\tn-us-va\tn-us-vt\t"
    "n-us-wa\tn-us-wi\tn-us-wv\tn-us-wy\tn-usa--\tn-usc--\tn-use--\tn-usl--\t"
    "n-usm--\tn-usn--\tn-uso--\tn-usp--\tn-usr--\tn-uss--\tn-ust--\tn-usu--\t"
    "n-xl---\tnc-----\tncbh---\tnccr---\tnccz---\tnces---\tncgt---\tncho---\t"
    "ncnq---\tncpn---\tnl-----\tnm-----\tnp-----\tnr-----\tnw-----\tnwaq---\t"
    "nwaw---\tnwbb---\tnwbf---\tnwbn---\tnwcj---\tnwco---\tnwcu---\tnwdq---\t"
    "nwdr---\tnweu---\tnwgd---\tnwgp---\tnwhi---\tnwht---\tnwjm---\tnwla---\t"
    "nwli---\tnwmj---\tnwmq---\tnwna---\tnwpr---\tnwsc---\tnwsd---\tnwsn---\t"
    "nwst---\tnwsv---\tnwtc---\tnwtr---\tnwuc---\tnwvb---\tnwvi---\tnwwi---\t"
    "nwxa---\tnwxi---\tnwxk---\tnwxm---\tp------\tpn-----\tpo-----\tpoas---\t"
    "pobp---\tpoci---\tpocw---\tpoea---\tpofj---\tpofp---\tpogg---\tpogu---\t"
    "poji---\tpokb---\tpoki---\tpoln---\tpome---\tpomi---\tponl---\tponn---\t"
    "ponu---\tpopc---\tpopl---\tpops---\tposh---\tpotl---\tpoto---\tpott---\t"
    "potv---\tpoup---\tpowf---\tpowk---\tpows---\tpoxd---\tpoxe---\tpoxf---\t"
    "poxh---\tps-----\tq------\tr------\ts------\ts-ag---\ts-bl---\ts-bo---\t"
    "s-ck---\ts-cl---\ts-ec---\ts-fg---\ts-gy---\ts-pe---\ts-py---\ts-sr---\t"
    "s-uy---\ts-ve---\tsa-----\tsn-----\tsp-----\tt------\tu------\tu-ac---\t"
    "u-at---\tu-at-ac\tu-at-ne\tu-at-no\tu-at-qn\tu-at-sa\tu-at-tm\tu-at-vi\t"
    "u-at-we\tu-atc--\tu-ate--\tu-atn--\tu-cs---\tu-nz---\tw------\tx------\t"
    "xa-----\txb-----\txc-----\txd-----\tzd-----\tzju----\tzma----\tzme----\t"
    "zmo----\tzne----\tzo-----\tzpl----\tzs-----\tzsa----\tzsu----\tzur----\t"
    "zve----"
)
"""Valid Geographic Area Codes tab-delimited string."""

GEOG_AREA_CODES: dict[str, int] = {
    code: 1 for code in GEOG_AREA_CODES_STR.split("\t") if code
}
"""Valid Geographic Area Codes lookup dict."""

OBSOLETE_GEOG_AREA_CODES_STR: str = (
    "t-ay---\te-ur-ai\te-ur-aj\tnwbc---\te-ur-bw\tf-by---\tpocp---\te-url--\t"
    "cr-----\tv------\te-ur-er\tet-----\te-ur-gs\tpogn---\tnwga---\tnwgs---\t"
    "a-hk---\tei-----\tf-if---\tawiy---\tawiw---\tawiu---\te-ur-kz\te-ur-kg\t"
    "e-ur-lv\te-ur-li\ta-mh---\tcm-----\te-ur-mv\tn-usw--\ta-ok---\ta-pt---\t"
    "e-ur-ru\tpory---\tnwsb---\tposc---\ta-sk---\tposn---\te-uro--\te-ur-ta\t"
    "e-ur-tk\te-ur-un\te-ur-uz\ta-vn---\ta-vs---\tnwvr---\te-urv--\ta-ys---"
)
"""Obsolete Geographic Area Codes tab-delimited string."""

OBSOLETE_GEOG_AREA_CODES = {
    code: 1 for code in OBSOLETE_GEOG_AREA_CODES_STR.split("\t") if code
}
"""Obsolete Geographic Area Codes lookup dict."""

LANGUAGE_CODES_STR: str = (
    "   \taar\tabk\tace\tach\tada\tady\tafa\tafh\tafr\tain\taka\takk\talb\t"
    "ale\talg\talt\tamh\tang\tanp\tapa\tara\tarc\targ\tarm\tarn\tarp\tart\t"
    "arw\tasm\tast\tath\taus\tava\tave\tawa\taym\taze\tbad\tbai\tbak\tbal\t"
    "bam\tban\tbaq\tbas\tbat\tbej\tbel\tbem\tben\tber\tbho\tbih\tbik\tbin\t"
    "bis\tbla\tbnt\tbos\tbra\tbre\tbtk\tbua\tbug\tbul\tbur\tbyn\tcad\tcai\t"
    "car\tcat\tcau\tceb\tcel\tcha\tchb\tche\tchg\tchi\tchk\tchm\tchn\tcho\t"
    "chp\tchr\tchu\tchv\tchy\tcmc\tcop\tcor\tcos\tcpe\tcpf\tcpp\tcre\tcrh\t"
    "crp\tcsb\tcus\tcze\tdak\tdan\tdar\tday\tdel\tden\tdgr\tdin\tdiv\tdoi\t"
    "dra\tdsb\tdua\tdum\tdut\tdyu\tdzo\tefi\tegy\teka\telx\teng\tenm\tepo\t"
    "est\tewe\tewo\tfan\tfao\tfat\tfij\tfil\tfin\tfiu\tfon\tfre\tfrm\tfro\t"
    "frr\tfrs\tfry\tful\tfur\tgaa\tgay\tgba\tgem\tgeo\tger\tgez\tgil\tgla\t"
    "gle\tglg\tglv\tgmh\tgoh\tgon\tgor\tgot\tgrb\tgrc\tgre\tgrn\tgsw\tguj\t"
    "gwi\thai\that\thau\thaw\theb\ther\thil\thim\thin\thit\thmn\thmo\thrv\t"
    "hsb\thun\thup\tiba\tibo\tice\tido\tiii\tijo\tiku\tile\tilo\tina\tinc\t"
    "ind\tine\tinh\tipk\tira\tiro\tita\tjav\tjbo\tjpn\tjpr\tjrb\tkaa\tkab\t"
    "kac\tkal\tkam\tkan\tkar\tkas\tkau\tkaw\tkaz\tkbd\tkha\tkhi\tkhm\tkho\t"
    "kik\tkin\tkir\tkmb\tkok\tkom\tkon\tkor\tkos\tkpe\tkrc\tkrl\tkro\tkru\t"
    "kua\tkum\tkur\tkut\tlad\tlah\tlam\tlao\tlat\tlav\tlez\tlim\tlin\tlit\t"
    "lol\tloz\tltz\tlua\tlub\tlug\tlui\tlun\tluo\tlus\tmac\tmad\tmag\tmah\t"
    "mai\tmak\tmal\tman\tmao\tmap\tmar\tmas\tmay\tmdf\tmdr\tmen\tmga\tmic\t"
    "min\tmis\tmkh\tmlg\tmlt\tmnc\tmni\tmno\tmoh\tmon\tmos\tmul\tmun\tmus\t"
    "mwl\tmwr\tmyn\tmyv\tnah\tnai\tnap\tnau\tnav\tnbl\tnde\tndo\tnds\tnep\t"
    "new\tnia\tnic\tniu\tnno\tnob\tnog\tnon\tnor\tnqo\tnso\tnub\tnwc\tnya\t"
    "nym\tnyn\tnyo\tnzi\toci\toji\tori\torm\tosa\toss\tota\toto\tpaa\tpag\t"
    "pal\tpam\tpan\tpap\tpau\tpeo\tper\tphi\tphn\tpli\tpol\tpon\tpor\tpra\t"
    "pro\tpus\tque\traj\trap\trar\troa\troh\trom\trum\trun\trup\trus\tsad\t"
    "sag\tsah\tsai\tsal\tsam\tsan\tsas\tsat\tscn\tsco\tsel\tsem\tsga\tsgn\t"
    "shn\tsid\tsin\tsio\tsit\tsla\tslo\tslv\tsma\tsme\tsmi\tsmj\tsmn\tsmo\t"
    "sms\tsna\tsnd\tsnk\tsog\tsom\tson\tsot\tspa\tsrd\tsrn\tsrp\tsrr\tssa\t"
    "ssw\tsuk\tsun\tsus\tsux\tswa\tswe\tsyc\tsyr\ttah\ttai\ttam\ttat\ttel\t"
    "tem\tter\ttet\ttgk\ttgl\ttha\ttib\ttig\ttir\ttiv\ttkl\ttlh\ttli\ttmh\t"
    "tog\tton\ttpi\ttsi\ttsn\ttso\ttuk\ttum\ttup\ttur\ttut\ttvl\ttwi\ttyv\t"
    "udm\tuga\tuig\tukr\tumb\tund\turd\tuzb\tvai\tven\tvie\tvol\tvot\twak\t"
    "wal\twar\twas\twel\twen\twln\twol\txal\txho\tyao\tyap\tyid\tyor\typk\t"
    "zap\tzbl\tzen\tzha\tznd\tzul\tzun\tzxx\tzza"
)
"""Valid Language Codes tab-delimited string."""

LANGUAGE_CODES: dict[str, int] = {
    code: 1 for code in LANGUAGE_CODES_STR.split("\t") if code
}
"""Valid Language Codes lookup dict."""

OBSOLETE_LANGUAGE_CODES_STR: str = (
    "ajm\tesk\tesp\teth\tfar\tfri\tgag\tgua\tint\tiri\tcam\tkus\tmla\tmax\t"
    "mol\tlan\tgal\tlap\tsao\tgae\tscc\tscr\tsho\tsnh\tsso\tswz\ttag\ttaj\t"
    "tar\ttru\ttsw"
)
"""Obsolete Language Codes tab-delimited string."""

OBSOLETE_LANGUAGE_CODES: dict[str, int] = {
    code: 1 for code in OBSOLETE_LANGUAGE_CODES_STR.split("\t") if code
}
"""Obsolete Language Codes lookup dict."""

COUNTRY_CODES_STR: str = (
    "aa \tabc\taca\tae \taf \tag \tai \taj \taku\talu\tam \tan \tao \taq \t"
    "aru\tas \tat \tau \taw \tay \tazu\tba \tbb \tbcc\tbd \tbe \tbf \tbg \t"
    "bh \tbi \tbl \tbm \tbn \tbo \tbp \tbr \tbs \tbt \tbu \tbv \tbw \tbx \t"
    "ca \tcau\tcb \tcc \tcd \tce \tcf \tcg \tch \tci \tcj \tck \tcl \tcm \t"
    "co \tcou\tcq \tcr \tctu\tcu \tcv \tcw \tcx \tcy \tdcu\tdeu\tdk \tdm \t"
    "dq \tdr \tea \tec \teg \tem \tenk\ter \tes \tet \tfa \tfg \tfi \tfj \t"
    "fk \tflu\tfm \tfp \tfr \tfs \tft \tgau\tgb \tgd \tgh \tgi \tgl \tgm \t"
    "go \tgp \tgr \tgs \tgt \tgu \tgv \tgw \tgy \tgz \thiu\thm \tho \tht \t"
    "hu \tiau\tic \tidu\tie \tii \tilu\tinu\tio \tiq \tir \tis \tit \tiv \t"
    "iy \tja \tji \tjm \tjo \tke \tkg \tkn \tko \tksu\tku \tkv \tkyu\tkz \t"
    "lau\tlb \tle \tlh \tli \tlo \tls \tlu \tlv \tly \tmau\tmbc\tmc \tmdu\t"
    "meu\tmf \tmg \tmiu\tmj \tmk \tml \tmm \tmnu\tmo \tmou\tmp \tmq \tmr \t"
    "msu\tmtu\tmu \tmv \tmw \tmx \tmy \tmz \tna \tnbu\tncu\tndu\tne \tnfc\t"
    "ng \tnhu\tnik\tnju\tnkc\tnl \tnmu\tnn \tno \tnp \tnq \tnr \tnsc\tntc\t"
    "nu \tnuc\tnvu\tnw \tnx \tnyu\tnz \tohu\toku\tonc\toru\tot \tpau\tpc \t"
    "pe \tpf \tpg \tph \tpic\tpk \tpl \tpn \tpo \tpp \tpr \tpw \tpy \tqa \t"
    "qea\tquc\trb \tre \trh \triu\trm \tru \trw \tsa \tsc \tscu\tsd \tsdu\t"
    "se \tsf \tsg \tsh \tsi \tsj \tsl \tsm \tsn \tsnc\tso \tsp \tsq \tsr \t"
    "ss \tst \tstk\tsu \tsw \tsx \tsy \tsz \tta \ttc \ttg \tth \tti \ttk \t"
    "tl \ttma\ttnu\tto \ttr \tts \ttu \ttv \ttxu\ttz \tua \tuc \tug \tuik\t"
    "un \tup \tutu\tuv \tuy \tuz \tvau\tvb \tvc \tve \tvi \tvm \tvp \tvra\t"
    "vtu\twau\twea\twf \twiu\twj \twk \twlk\tws \twvu\twyu\txa \txb \txc \t"
    "xd \txe \txf \txga\txh \txj \txk \txl \txm \txn \txna\txo \txoa\txp \t"
    "xr \txra\txs \txv \txx \txxc\txxk\txxu\tye \tykc\tza "
)
"""Valid Country Codes tab-delimited string."""

COUNTRY_CODES: dict[str, int] = {
    code.strip(): 1 for code in COUNTRY_CODES_STR.split("\t") if code
}
"""Valid Country Codes lookup dict."""

OBSOLETE_COUNTRY_CODES_STR: str = (
    "ai \tair\tac \tajr\tbwr\tcn \tcz \tcp \tln \tcs \terr\tgsr\tge \tgn \t"
    "hk \tiw \tiu \tjn \tkzr\tkgr\tlvr\tlir\tmh \tmvr\tnm \tpt \trur\try \t"
    "xi \tsk \txxr\tsb \tsv \ttar\ttt \ttkr\tunr\tuk \tui \tus \tuzr\tvn \t"
    "vs \twb \tys \tyu "
)
"""Obsolete Country Codes tab-delimited string."""

OBSOLETE_COUNTRY_CODES: dict[str, int] = {
    code.strip(): 1 for code in OBSOLETE_COUNTRY_CODES_STR.split("\t") if code
}
"""Obsolete Country Codes lookup dict."""
