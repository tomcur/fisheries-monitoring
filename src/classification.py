import os
import functools
import json
import numpy as np
import main
import settings
import pipeline

class FullClassification:
    """
    A class to perform classification on a set of images, using various (pre-trained) parts.
    """

    def __init__(self, dataset = "test"):
        """
        :param dataset: "test" or "final"
        """
        self.dataset = dataset
        self.prepare_directories()

    def prepare_directories(self):
        if self.dataset == "test":
            self.fish_or_no_fish_classification_dir = settings.TEST_FISH_OR_NO_FISH_CLASSIFICATION_DIR
            self.fish_type_classification_dir = settings.TEST_FISH_TYPE_CLASSIFICATION_DIR
        elif self.dataset == "final":
            pass # not yet implemented

    def propose_candidates(self):
        """
        Stage 1
        """
        main.segment_dataset(self.dataset)

    def crop_candidates(self):
        """
        Stage 2
        """
        main.crop_images(self.dataset, crop_type = "candidates")

    def classify_fish_or_no_fish(self):
        """
        Stage 3
        """

        import keras

        pipeline = pipeline.Pipeline(data_type = "candidates_cropped", dataset = self.dataset)

        # Load fish-or-no-fish classification model
        model = keras.models.load_model(os.path.join(settings.WEIGHTS_DIR, settings.FISH_OR_NO_FISH_CLASSIFICATION_NETWORK_WEIGHT_NAME))

        data_generator = self.pipeline.data_generator_builder(
            functools.partial(self.pl.mini_batch_generator, mini_batch_size = 32))

        predicted = {}

        # For each batch
        for x, y, meta in data_generator:
            x = np.array(x)

            predictions = model.predict(x, batch_size = 32)

            for m, pred in zip(meta, list(predictions)):
                predicted[m['filename']] = bool(pred)

        # Save classifications
        with open(os.path.join(self.fish_or_no_fish_classification_dir, "classification.json"), 'w') as outfile:
            json.dump(predicted, outfile)

    def classify_fish_type(self):
        """
        Stage 4
        """

        import keras

        pipeline = pipeline.Pipeline(data_type = "candidates_cropped", dataset = self.dataset)

        # Load fish type classification model
        model = keras.models.load_model(os.path.join(settings.WEIGHTS_DIR, settings.FISH_TYPE_CLASSIFICATION_NETWORK_WEIGHT_NAME))

        # Load fish-or-no-fish classifications
        with open(os.path.join(self.fish_or_no_fish_classification_dir, "classification.json"), 'r') as infile:
            fish_or_no_fish = json.load(infile)

        data = self.pipeline.get_data()

        fish_type_classification = {}

        # For each single crop
        for x, meta in zip(data['x'], data['meta']):
            x = np.array(x)

            if fish_or_no_fish[meta['filename']]:

                img = x()
                img = np.array([img])

                predictions = model.predict(img, batch_size = 1)
                prediction = predictions[0]

                fish_type_classification[meta['filename']] = prediction
    
        # Save classifications
        with open(os.path.join(self.fish_type_classification_dir, "classification.json"), 'w') as outfile:
            json.dump(fish_type_classification, outfile)

    def classify_image(self):
        """
        Stage 5
        """

        # Load fish type classifications
        with open(os.path.join(self.fish_type_classification_dir, "classification.json"), 'r') as infile:
            fish_type_classification = json.load(infile)

        pipeline = pipeline.Pipeline(data_type = "candidates_cropped", dataset = self.dataset)
        data = self.pipeline.get_data()


        img_classifications = {}
        # Aggregate classifications of bounding boxes to original image level
        for meta in data['meta']:
            name = meta['filename']

            if name in fish_type_classification:
                # There is a classification for this crop

                original_img = meta['original_image']

                if original_img not in img_classifications:
                    img_classifications = []

                img_classifications.append(fish_type_classification[name])

        # Perform something to turn list of classifications for an image to a single class...
        img_classification = {}

        pipeline_original = pipeline.Pipeline(data_type = "original", dataset = self.dataset)
        original_images = pipeline_original.get_data()
        for meta in original_images['meta']:
            name = meta['filename']

            if name not in img_classifications:
                img_classification['name'] = settings.CLASS_NAME_TO_INDEX_MAPPING["NoF"]
            else:
                classifications = img_classifications[name]
                # Use classifications to generate a single classification
                
        # Output in kaggle format...
