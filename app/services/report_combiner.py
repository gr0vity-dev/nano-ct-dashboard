from app.services.data_processor import IProcessor

class DataCombiner:

    def __init__(self, processors):
        self.processors = processors

        # This can be expanded to decouple the input keys from the resulting keys.

    def combine_data_as_dict(self):

        combined_data = {}

        processor: IProcessor
        for processor in self.processors:
            processor.process_all()
            processor.merge_to(combined_data)
        return combined_data


    def combine_data(self):
        combined_data = self.combine_data_as_dict()
        sorted_data = sorted(combined_data.values(), key=lambda x: x.get('built_at', x.get('created_at', '1970-01-01T00:00:00Z')), reverse=True)
        return sorted_data
