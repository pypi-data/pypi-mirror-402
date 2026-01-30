## Dummy NotebookUtils/MsSparkUtils for Python

This is a pure dummy interfaces package which mirrors [MsSparkUtils' APIs](https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/microsoft-spark-utilities?pivots=programming-language-r) of [Azure Synapse Analytics](https://learn.microsoft.com/en-us/azure/synapse-analytics/) for python users,customer of Azure Synapse Analytics can download this package from PyPi to generate the build.

## Getting started
Install dummy_notebookutils with pip:

```shell
pip install dummy-notebookutils
```
## Examples
```
from notebookutils import mssparkutils
mssparkutils.fs.ls("/")
```
> NOTICE: again, the package only mirrors APIs of synapse mssparkutils without actual functionality. The main goal is to help customer generating the local build. You always need upload your built package to synapse workspace for end to end testing.
