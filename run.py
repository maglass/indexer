import logging
import sys
from time import sleep

import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch import helpers


def bulk(_client, _index_name, _collection_path, _header_path, sleep_time=0.5):
    fields = _get_fields(_header_path)
    with open(_collection_path, 'r', encoding='utf8') as rf:
        buffer = list()
        for line in rf:
            values = line.rstrip('\n').split('\t')
            _id, doc = _p_doc(fields, values)
            buffer.append(doc)
            if 100 <= len(buffer):
                _flush(_client, _index_name, buffer)
                sleep(sleep_time)

    _flush(_client, _index_name, buffer)


def _flush(_client, _index_name, _buffer):
    logging.info('indexing {}'.format(len(_buffer)))
    actions = list()
    for bb in _buffer:
        doc = {
            '_index': _index_name,
            '_type': '_doc',
            '_id': bb['video_id'],
        }
        doc.update(bb)
        actions.append(doc)

    elasticsearch.helpers.bulk(_client, actions)
    _buffer[:] = list()


def _create_index(_client, _index_name, _version):
    if _client.indices.exists(_index_name):
        _client.indices.delete(_index_name)
    body = _get_index_create_template(version)
    _client.indices.create(_index_name, body=body)


def _get_index_create_template(version):
    with open('templates/index-template-{}.json'.format(version), 'r') as rf:
        template = rf.read()
        return template


def _get_fields(path):
    rf = open(path, 'r', encoding='utf8')
    line = rf.readline()
    rf.close()
    return line.strip().split(',')


def _p_doc(_fields, _values):
    _doc = {ff: vv for ff, vv in zip(_fields, _values)}
    doc_id = _doc['video_id']
    return doc_id, _doc


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    argv = sys.argv[1:]
    collection_path = argv[0]
    header_path = argv[1]
    version = argv[2]

    client = Elasticsearch(hosts='http://13.125.252.81:9200')

    index_name = 'collection-{}'.format(version)
    _create_index(client, index_name, version)

    bulk(client, index_name, collection_path, header_path)
