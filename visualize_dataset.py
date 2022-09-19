import fiftyone as fo

# A name for the dataset
name = "artificial-comics"

# The directory containing the dataset to import
dataset_dir = "output_ds"

# The type of the dataset being imported
dataset_type = fo.types.COCODetectionDataset 

fo.delete_dataset(name)

dataset = fo.Dataset.from_dir(
    dataset_dir=dataset_dir,
    dataset_type=dataset_type,
    name=name,
    label_types="segmentations"
)

session = fo.launch_app(dataset)
session.wait()