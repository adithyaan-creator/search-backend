from haystack.preprocessor.cleaning import clean_wiki_text
from haystack.file_converter.pdf import PDFToTextConverter
from haystack.preprocessor.preprocessor import PreProcessor
from haystack.preprocessor.utils import convert_files_to_dicts, fetch_archive_from_http
from haystack.retriever.dense import EmbeddingRetriever
from haystack.retriever.sparse import TfidfRetriever
from haystack.retriever.dense import EmbeddingRetriever
from haystack.document_store.memory import InMemoryDocumentStore
from haystack.document_store.elasticsearch import ElasticsearchDocumentStore
from haystack.pipeline import DocumentSearchPipeline, ExtractiveQAPipeline
from haystack.reader.farm import FARMReader

class InformationRetriever:
    def __init__(self):
        use_cuda = True
        #self.reader = FARMReader(model_name_or_path="distilbert-base-uncased-distilled-squad", use_gpu=use_cuda)
        self.document_store = InMemoryDocumentStore() 
        self.processor = PreProcessor(clean_empty_lines=True, clean_whitespace=True, clean_header_footer=True, split_by="word", split_length=50, split_respect_sentence_boundary=True, split_overlap=0)   
        self.converter = PDFToTextConverter(remove_numeric_tables=True, valid_languages=["en"])
        #self.embedding_model = EmbeddingRetriever(document_store=self.document_store, embedding_model="sentence-transformers/msmarco-distilroberta-base-v2")
        #self.document_store = ElasticsearchDocumentStore(host="localhost", username="", password="", index="document")

    def extract_from_pdf(self, document_path):
        #try:
        doc = self.converter.convert(file_path=document_path)
        return doc
        #except:
        #    return {'error converting document'}

    def preprocess(self, doc):
        #try:
        docs = self.processor.process(doc)
        return docs
        #except:
        #    return {'error preprocessing document'}

    def create_el_index(self, index_name):
        ## creates index in elasticsearch for each user based on his user_id
        user_index_name = index_name
        self.document_store._create_document_index(user_index_name)
        return

    def index(self, docs, index_metadata, useDense):
        dicts = []
        for i in (docs):
            dicts.append({"text": str(i), "meta" : index_metadata})
        self.document_store.write_documents(dicts)#, index=user_id)
        #if useDense:
        #    self.document_store.update_embeddings(self.embedding_model)
        return 

    def get_doc_count(self):
        count = self.document_store.get_document_count()
        return count

    def delete_all(self):#,filters):
        self.document_store.delete_all_documents()
        return 'data deleted'

    def retrieve(self, query, k_retrievers, useDense):#, filters):
         #filter in format {'user_id': user_id, 'document_id': document_id}
        retriever_tfid = TfidfRetriever(document_store=self.document_store)
        #if useDense:
        #    pipe = DocumentSearchPipeline(self.embedding_model)
        #else:
        #    pipe = DocumentSearchPipeline(retriever_tfid)

        pipe = DocumentSearchPipeline(retriever_tfid)        
        
        out = pipe.run(query=query, top_k_retriever=int(k_retrievers))#, filters=filters)
        for i in out['documents']:
            del i['embedding']
            del i['score']
            del i['probability']
            del i['question']
            #del (i['meta']['user_id'])
            #del i['meta']['document_id']
            #del i['meta']['document_id']

        
        return out
    
    '''def answer(self, query, filters, k_retrievers, k_readers):
        retriever_tfid = TfidfRetriever(document_store=self.document_store)
        pipe = ExtractiveQAPipeline(ir_obj.reader, retriever_tfid)
        out = pipe.run(query=query, top_k_retriever=int(k_retrievers), filters=filters)
        pass'''