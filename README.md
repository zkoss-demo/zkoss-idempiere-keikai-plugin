# ZKoss Keikai Plugin for iDempiere

This repository packages Keikai Spreadsheet for iDempiere using the OSGi fragment + plugin pattern.

It is created for the local iDempiere 13 workspace at `/Users/jameschu/zkworks/idempiere-13` and targets Keikai `6.3.0-Eval`.

This plugin structure follows the ZKoss iDempiere EE plugin guide:
[IDEMPIERE_NEW_PLUGIN_GUIDE.md](https://github.com/zkoss-demo/zkoss-idempiere-ee-plugin/blob/main/docs/IDEMPIERE_NEW_PLUGIN_GUIDE.md).

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
| Keikai target | `6.3.0-Eval` with `keikai-ex` and `keikai-pdf` |

Keikai `6.3.0-Eval` declares ZK `10.3.0.1-Eval` in its parent POM, while this iDempiere workspace ships ZK `10.0.1`. The plugin uses the ZK `10.0.1-Eval` `zkex` jar to stay aligned with the iDempiere ZK host. Runtime compatibility still needs to be verified in the server.

The `keikai-ex` jar is included because the base Keikai jar marks some toolbar actions, such as Save Book, as available only in Keikai EE. The optional `keikai-pdf` jar and its `openpdf` dependency are included so `Exporters.getExporter("pdf")` can provide the native Keikai PDF exporter. The fragment registers the PDF exporter with `pdf=io.keikai.model.impl.pdf.PdfExporterFactory` in `src/metainfo/zk/zk.xml`.

The example uses `Executions.createComponents("~./keikai-form.zul", ...)` for ZUL loading, matching the usual iDempiere form pattern. The spreadsheet workbook uses `src="web/blank.xlsx"` instead of `~./blank.xlsx` because Keikai resolves `Spreadsheet.setSrc()` through its workbook loader, not through the same ZK component-creation path.

## Build

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

## Runtime

Install both generated jars into the iDempiere OSGi runtime:

- `org.idempiere.keikai.fragment/target/org.idempiere.keikai.fragment-13.0.0-SNAPSHOT.jar`
- `org.idempiere.keikai.example/target/org.idempiere.keikai.example-13.0.0-SNAPSHOT.jar`

The fragment should resolve against `org.adempiere.ui.zk`; the example plugin should become active and import its `META-INF/2Pack_*.zip` registration.

After changing fragment jars or `src/metainfo/zk/zk.xml`, restart the iDempiere web application or OSGi runtime. ZK reads library properties during webapp initialization, so the PDF exporter registration is not reliably picked up by hot-swapping only the example bundle.
