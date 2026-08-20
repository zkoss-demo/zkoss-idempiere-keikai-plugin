# ZKoss Keikai EE Eval Plugin for iDempiere

This repository packages the Keikai EE Eval version of Keikai Spreadsheet for iDempiere using the OSGi fragment + plugin pattern.

It is created for the local iDempiere 13 workspace at `/Users/jameschu/zkworks/idempiere-13` and targets Keikai EE Eval `6.3.0-Eval`.

This plugin structure follows the ZKoss iDempiere EE plugin guide:
[IDEMPIERE_NEW_PLUGIN_GUIDE.md](https://github.com/zkoss-demo/zkoss-idempiere-ee-plugin/blob/main/docs/IDEMPIERE_NEW_PLUGIN_GUIDE.md).

## Creation Notes

This plugin was generated from the generic iDempiere ZK EE / addon plugin pattern, with Keikai-specific module inputs. Keikai is not a single-addon-jar case: the fragment must include the base Keikai runtime plus feature modules such as `keikai-ex` and `keikai-pdf`.

When recreating or updating this plugin with an AI agent, provide the required Keikai modules explicitly and keep the module list synchronized across:

- `org.idempiere.keikai.fragment/pom.xml` dependency-copy artifacts
- `org.idempiere.keikai.fragment/META-INF/MANIFEST.MF` `Bundle-ClassPath`
- `org.idempiere.keikai.fragment/build.properties` `bin.includes`
- `org.idempiere.keikai.fragment/src/metainfo/zk/zk.xml` for Keikai-specific ZK library properties such as the PDF exporter

## Modules

| Module | Purpose |
|---|---|
| `org.idempiere.keikai.fragment` | Attaches Keikai runtime jars to `org.adempiere.ui.zk` so ZK can discover Keikai resources, components, and the PDF exporter |
| `org.idempiere.keikai.example` | Registers a small iDempiere form that renders a Keikai spreadsheet component loaded from `web/blank.xlsx`, with New Book, Save Book, and Export PDF toolbar actions enabled |

## Version Notes

The local iDempiere 13 core currently declares:

| Item | Value |
|---|---|
| iDempiere | `13.0.0-SNAPSHOT` |
| Tycho | `4.0.8` |
| Java execution environment | `JavaSE-17` |
| ZK CE in iDempiere | `10.0.1` |
| Keikai target | Keikai EE Eval `6.3.0-Eval` with `keikai-ex` and `keikai-pdf` |

This plugin is intentionally built with Keikai EE Eval artifacts, not Keikai CE artifacts or production-licensed EE artifacts. Keikai EE Eval `6.3.0-Eval` declares ZK `10.3.0.1-Eval` in its parent POM, while this iDempiere workspace ships ZK `10.0.1`. The plugin uses the ZK `10.0.1-Eval` `zkex` jar to stay aligned with the iDempiere ZK host. Runtime compatibility still needs to be verified in the server.

The `keikai-ex` jar is included because the base Keikai jar marks some toolbar actions, such as Save Book, as available only in Keikai EE. The optional `keikai-pdf` jar and its `openpdf` dependency are included so `Exporters.getExporter("pdf")` can provide the native Keikai PDF exporter. The fragment registers the PDF exporter with `pdf=io.keikai.model.impl.pdf.PdfExporterFactory` in `src/metainfo/zk/zk.xml`.

The example uses `Executions.createComponents("~./keikai-form.zul", ...)` for ZUL loading, matching the usual iDempiere form pattern. The spreadsheet workbook uses `src="web/blank.xlsx"` instead of `~./blank.xlsx` because Keikai resolves `Spreadsheet.setSrc()` through its workbook loader, not through the same ZK component-creation path.

## Installing

You need a running iDempiere 13 instance - for example the
[official Docker image](https://hub.docker.com/r/idempiereofficial/idempiere).

Prebuilt jars are attached to each [release](https://github.com/zkoss-demo/zkoss-idempiere-keikai-plugin/releases), so nothing has to be built to try the
plugin:

| File | Purpose |
|---|---|
| `org.idempiere.keikai.fragment-13.0.0.jar` | The Keikai fragment. **Required.** |
| `org.idempiere.keikai.example-13.0.0.jar` | The example form. Optional. |

Install both into the iDempiere OSGi runtime, the fragment first.

The fragment should resolve against `org.adempiere.ui.zk`; the example plugin should become active and import its `META-INF/2Pack_*.zip` registration.

After changing fragment jars or `src/metainfo/zk/zk.xml`, restart the iDempiere web application or OSGi runtime. ZK reads library properties during webapp initialization, so the PDF exporter registration is not reliably picked up by hot-swapping only the example bundle.

For the other ways to get a bundle into a runtime - p2 repository, Gogo shell, dropping it into
the plugins directory - see iDempiere's [Distributing and Installing Plug-ins](https://docs.idempiere.org/docs/basic-development/plugin-development/distributing-plugins).

To build the jars yourself instead, see [Building from source](#building-from-source) below.

---

## Building from source

Only needed if you want to change the code. To install and try the plugin, download the jars
attached to a release, as described under [Installing](#installing).

Build from the repository root:

```bash
cd /Users/jameschu/zkworks/idempiere-13/zkoss-idempiere-keikai-plugin
mvn clean verify -f parent-repository-pom.xml
```

After `validate`, verify the fragment jars and metadata stay aligned:

```bash
cd org.idempiere.keikai.fragment
find lib -maxdepth 1 -type f -name '*.jar' -exec basename {} \; | sort
rg 'lib/.*\.jar' META-INF/MANIFEST.MF build.properties
```

Every jar in `Bundle-ClassPath` must exist under `lib/`.

### Publishing a release

`./make-release.sh` collects every built jar into a local `release/` folder, dropping the
`-SNAPSHOT` from the file name. That folder is git-ignored: upload its contents as attachments
on the GitHub release page rather than committing them.

The file name comes from the Maven version, which stays `13.0.0-SNAPSHOT`; the version OSGi
actually uses is the `Bundle-Version` inside the jar, where `.qualifier` has been expanded to
a build timestamp such as `13.0.0.202608190118`. Every build therefore gets a distinct OSGi
version - Felix sees a rebuild as newer and updates it - while the published file stays
`...-13.0.0.jar`.

## License

**The plugin source code** in this repository is licensed under the
[GNU General Public License v2.0](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) or
later, the same license iDempiere itself uses. See [LICENSE.md](LICENSE.md).

**The source tree contains no Keikai or ZK binaries.** The fragment declares them as Maven
dependencies; the build downloads them from ZK's Evaluation repository into a git-ignored `lib/`.

**The released jars are a different matter.** A fragment's whole job is to put those jars on the
host bundle's class loader, so the built fragment embeds all of them:

| Released jar | Contains | Redistributable under the GPL? |
|---|---|---|
| `org.idempiere.keikai.example` | Only this project's own compiled code | Yes - GPLv2 or later |
| `org.idempiere.keikai.fragment` | 28 jars, ~54 MB: **Keikai EE Evaluation** and `zkex` / `zkcharts` Evaluation, plus Apache POI, `openpdf`, `jfreechart` and other third-party libraries | **No** - the Keikai and ZK jars are governed by ZK's license, not the GPL; the rest keep their own open-source licenses |

| Component | License |
|---|---|
| This project's source and its own compiled bundle | GPLv2 or later |
| [Keikai](https://keikai.io/) EE (`keikai`, `keikai-ex`, `keikai-pdf`, `keikai-model`) | Commercial - Evaluation builds are used here |
| `zkex`, `zkcharts` | Commercial - carried by the fragment because Keikai needs them |
| Apache POI (`io.keikai:poi`), `openpdf`, `jfreechart`, `commons-*`, `xmlbeans`, `jsoup`, `byte-buddy` and the rest | Their own open-source licenses, redistributed unmodified - **itemized in [THIRD-PARTY.md](THIRD-PARTY.md)** |
| ZK CE (in iDempiere) | LGPL - already part of iDempiere, unchanged by this plugin |

[THIRD-PARTY.md](THIRD-PARTY.md) lists every embedded jar with its coordinates, size and license,
and is regenerated from the built `lib/` by `./make-third-party.py`. `make-release.sh` copies it,
and `LICENSE.md`, into `release/` so both travel with the jars. Three of the embedded libraries -
`jfreechart`, `jcommon` and `openpdf` - are **LGPL**, which attaches obligations that Apache-2.0
and MIT do not; see the note at the end of that file before publishing a release publicly.

**What you may do with a downloaded fragment.** Install it and evaluate it. The Evaluation
binaries inside are provided for evaluation only: they are not yours to redistribute, and a valid
Keikai EE license or subscription is required before use in production. Contact
<info@zkoss.org>.

**One caveat when backing out.** Removing the fragment leaves iDempiere core untouched, but any
form *you* wrote against the spreadsheet component stops working with it.

---

## See also

Three repositories bring ZK commercial products into iDempiere. All three use the same
OSGi **fragment + plugin** pattern; they differ only in which jars the fragment carries.

| Repository | Brings in | Start there when you want |
|---|---|---|
| **This repository** | Keikai Spreadsheet (`keikai`, `keikai-ex`, `keikai-pdf`) | An Excel-compatible spreadsheet inside an iDempiere form |
| [zkoss-idempiere-ee-plugin](https://github.com/zkoss-demo/zkoss-idempiere-ee-plugin) | ZK EE (`zkex`, `zkmax`, `client-bind`, `zuti`, `za11y`) | The general ZK EE component set. Its [new-plugin guide](https://github.com/zkoss-demo/zkoss-idempiere-ee-plugin/blob/main/docs/IDEMPIERE_NEW_PLUGIN_GUIDE.md) is the pattern this repository was generated from |
| [zkoss-idempiere-zkcharts-plugin](https://github.com/zkoss-demo/zkoss-idempiere-zkcharts-plugin) | ZK Charts, ZK Pivottable | Charts and pivot tables - including replacing iDempiere's built-in chart rendering globally. Its README also documents the OSGi class-loader pitfalls a ZK component hits when it loads its own ZUL |

The three fragments target the same host bundle, `org.adempiere.ui.zk`. OSGi allows a host
any number of fragments, so they can be installed side by side - but check for overlap
first: the Keikai fragment carries its own `zkex` and `zkcharts`, and not necessarily at
the same versions as the other two fragments ship. Each fragment needs a restart to attach.
