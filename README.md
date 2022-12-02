# Data Coordination Quality Control (DCQC) - Proof of Concept

This repository contains a proof of concept that demonstrates how a Nextflow workflow can be orchestrated by a Python script. In this case, the Python code determines which QC tests need to happen for each files and "queues" them up in Nextflow. Some of these tests are performed by the Python script (_i.e._ internal QC tests), whereas others require running a command in a separate container and interpreting the log files (_i.e._ external QC tests). In both cases, the Python script then collates the test results into JSON reports, both at the file level and the dataset level.

![DCQC](assets/dcqc.png)

## Usage

You first need access to the Synapse files listed in `data/input_all.csv`. Then, you can run the following command after cloning the repository: 

```console
nextflow run main.nf -profile test_all,docker
```

## Example Output

```json
[
  {
    "target": {
      "type": "FileQcTarget",
      "uri": "syn://syn26644414",
      "metadata": {
        "file_type": "ome.tif",
        "md5_checksum": "0a3d8f1d2d69f15aeccedea0d54efa6c"
      },
      "files": [
        {
          "uri": "syn://syn26644414",
          "type": "SynapseFile",
          "version": 1,
          "filename": "HTMA402_2-001.ome.tif",
          "synapse_id": "syn26644414"
        }
      ]
    },
    "summary_status": {
      "required_tests": [
        "FileExtensionQcTest",
        "LibTiffInfoQcTest",
        "Md5ChecksumQcTest",
        "OmeXmlSchemaQcTest"
      ],
      "status": false
    },
    "tests": [
      {
        "type": "FileExtensionQcTest",
        "config": {
          "file_extensions": [
            ".ome.tif",
            ".ome.tiff"
          ]
        },
        "tier": 1,
        "is_internal_test": true,
        "status": true
      },
      {
        "type": "LibTiffInfoQcTest",
        "config": {},
        "tier": 2,
        "is_internal_test": false,
        "status": false
      },
      {
        "type": "Md5ChecksumQcTest",
        "config": {},
        "tier": 1,
        "is_internal_test": true,
        "status": true
      },
      {
        "type": "OmeXmlSchemaQcTest",
        "config": {},
        "tier": 2,
        "is_internal_test": false,
        "status": false
      }
    ]
  },
  {
    "target": {
      "type": "FileQcTarget",
      "uri": "syn://syn26644421",
      "metadata": {
        "file_type": "ome.tif",
        "md5_checksum": "313257a6822ff5b52e7e35a626b6c33f"
      },
      "files": [
        {
          "uri": "syn://syn26644421",
          "type": "SynapseFile",
          "version": 1,
          "filename": "HTMA402_2-003.ome.tif",
          "synapse_id": "syn26644421"
        }
      ]
    },
    "summary_status": {
      "required_tests": [
        "FileExtensionQcTest",
        "LibTiffInfoQcTest",
        "Md5ChecksumQcTest",
        "OmeXmlSchemaQcTest"
      ],
      "status": false
    },
    "tests": [
      {
        "type": "FileExtensionQcTest",
        "config": {
          "file_extensions": [
            ".ome.tif",
            ".ome.tiff"
          ]
        },
        "tier": 1,
        "is_internal_test": true,
        "status": true
      },
      {
        "type": "LibTiffInfoQcTest",
        "config": {},
        "tier": 2,
        "is_internal_test": false,
        "status": false
      },
      {
        "type": "Md5ChecksumQcTest",
        "config": {},
        "tier": 1,
        "is_internal_test": true,
        "status": true
      },
      {
        "type": "OmeXmlSchemaQcTest",
        "config": {},
        "tier": 2,
        "is_internal_test": false,
        "status": false
      }
    ]
  },
  {
    "target": {
      "type": "FileQcTarget",
      "uri": "syn://syn41864974",
      "metadata": {
        "file_type": "txt",
        "md5_checksum": "38b86a456d1f441008986c6f798d5ef9"
      },
      "files": [
        {
          "uri": "syn://syn41864974",
          "type": "SynapseFile",
          "version": 6,
          "filename": "newline.txt",
          "synapse_id": "syn41864974"
        }
      ]
    },
    "summary_status": {
      "required_tests": [
        "FileExtensionQcTest",
        "Md5ChecksumQcTest"
      ],
      "status": true
    },
    "tests": [
      {
        "type": "FileExtensionQcTest",
        "config": {
          "file_extensions": [
            ".txt"
          ]
        },
        "tier": 1,
        "is_internal_test": true,
        "status": true
      },
      {
        "type": "Md5ChecksumQcTest",
        "config": {},
        "tier": 1,
        "is_internal_test": true,
        "status": true
      }
    ]
  },
  {
    "target": {
      "type": "FileQcTarget",
      "uri": "syn://syn41864977",
      "metadata": {
        "file_type": "txt",
        "md5_checksum": "a542e9b744bedcfd874129ab0f98c4ff"
      },
      "files": [
        {
          "uri": "syn://syn41864977",
          "type": "SynapseFile",
          "version": 1,
          "filename": "no-newline.txt",
          "synapse_id": "syn41864977"
        }
      ]
    },
    "summary_status": {
      "required_tests": [
        "FileExtensionQcTest",
        "Md5ChecksumQcTest"
      ],
      "status": true
    },
    "tests": [
      {
        "type": "FileExtensionQcTest",
        "config": {
          "file_extensions": [
            ".txt"
          ]
        },
        "tier": 1,
        "is_internal_test": true,
        "status": true
      },
      {
        "type": "Md5ChecksumQcTest",
        "config": {},
        "tier": 1,
        "is_internal_test": true,
        "status": true
      }
    ]
  },
  {
    "target": {
      "type": "FileQcTarget",
      "uri": "syn://syn43716055",
      "metadata": {
        "file_type": "tif",
        "md5_checksum": "38b86a456d1f441008986c6f798d5ef9"
      },
      "files": [
        {
          "uri": "syn://syn43716055",
          "type": "SynapseFile",
          "version": 1,
          "filename": "new line.txt",
          "synapse_id": "syn43716055"
        }
      ]
    },
    "summary_status": {
      "required_tests": [
        "FileExtensionQcTest",
        "LibTiffInfoQcTest",
        "Md5ChecksumQcTest"
      ],
      "status": false
    },
    "tests": [
      {
        "type": "FileExtensionQcTest",
        "config": {
          "file_extensions": [
            ".tif",
            ".tiff"
          ]
        },
        "tier": 1,
        "is_internal_test": true,
        "status": false
      },
      {
        "type": "LibTiffInfoQcTest",
        "config": {},
        "tier": 2,
        "is_internal_test": false,
        "status": false
      },
      {
        "type": "Md5ChecksumQcTest",
        "config": {},
        "tier": 1,
        "is_internal_test": true,
        "status": true
      }
    ]
  },
  {
    "target": {
      "type": "FileQcTarget",
      "uri": "syn://syn43716711",
      "metadata": {
        "file_type": "tif",
        "md5_checksum": "a542e9b744bedcfd874129ab0f98c4ff"
      },
      "files": [
        {
          "uri": "syn://syn43716711",
          "type": "SynapseFile",
          "version": 1,
          "filename": "no newline.txt",
          "synapse_id": "syn43716711"
        }
      ]
    },
    "summary_status": {
      "required_tests": [
        "FileExtensionQcTest",
        "LibTiffInfoQcTest",
        "Md5ChecksumQcTest"
      ],
      "status": false
    },
    "tests": [
      {
        "type": "FileExtensionQcTest",
        "config": {
          "file_extensions": [
            ".tif",
            ".tiff"
          ]
        },
        "tier": 1,
        "is_internal_test": true,
        "status": false
      },
      {
        "type": "LibTiffInfoQcTest",
        "config": {},
        "tier": 2,
        "is_internal_test": false,
        "status": false
      },
      {
        "type": "Md5ChecksumQcTest",
        "config": {},
        "tier": 1,
        "is_internal_test": true,
        "status": true
      }
    ]
  }
]
```
