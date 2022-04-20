import unittest
import json
from django.test import TestCase
from main.assets.services.managers import FileManager, SectionManager


class FileManagerTest(TestCase):
    """
    4. File Manager
    """

    def test_index_file(self):
        """
        (a) Verify that index_file assigns pages to the correct sections
        """
        file = FileManager("this is a placeholder file")
        file.index = {
            "Important Notice": 2,
            "Contents": 3,
            "Section 1": 5,
        }
        file.pages = {
            0: "this is page 0",
            1: "this is page 1",
            2: "this is page 2",
            3: "this is page 3",
            4: "this is page 4",
            5: "this is page 5",
            6: "this is page 6",
        }

        expected = {
            None: {
                0: "this is page 0",
                1: "this is page 1",
            },
            "Important Notice": {
                2: "this is page 2",
            },
            "Contents": {
                3: "this is page 3",
                4: "this is page 4",
            },
            "Section 1": {
                5: "this is page 5",
                6: "this is page 6",
            }
        }
        file._index_pages()
        output = file.contents

        # ASSERTIONS
        # (a)
        self.assertEqual(expected, output)

    def test_create_page_json(self):
        """
        (b) Verify that create_page_json creates a dictionary of the
        correct layout with the correct details
        """
        page_section = "section name"
        page_number = 22
        page_name = "page name"
        page_text = "this is the page text \n" \
                    "this text has a page name and a section name\n" \
                    "section name|page name\n" \
                    "this is page 22\n"
        manager = FileManager("this is a placeholder file")
        output = manager._create_page_json(page_section, page_number,
                                           page_name,
                                           page_text)
        time = output['_source']['timestamp']
        expected = {
            "_index": manager.index_name,
            "_type": "page",
            "_id": manager.index_name + str(page_number),
            "_source": {
                "timestamp": time,
                "page_number": page_number,
                "section": page_section,
                "name": page_name,
                "body": page_text
            }
        }

        # ASSERTIONS
        # (b)
        self.assertEqual(expected, output)

    def test_build_query(self):
        """
        (c) Verify that build_query compiles the correct query
        """
        class FakeKeyword:
            def __init__(self, keyword, alts):
                self.keyword = keyword
                self.alternatives = alts

            def alt_list(self, string=False):
                if string:
                    alts = self.alternatives
                    alts.append(self.keyword)
                    return alts

        fake_keywords = [
            FakeKeyword("assets", []),
            FakeKeyword("total", [])
        ]
        expected = json.dumps(
            {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "bool": {
                                    "should": [
                                        {

                                            "match_phrase": {
                                                "body": {
                                                    "query": "assets",
                                                    "boost": 1
                                                }
                                            }
                                        }, {
                                            "match_phrase": {
                                                "section": {
                                                    "query": "assets",
                                                    "boost": 0.5
                                                }
                                            }
                                        }, {
                                            "match_phrase": {
                                                "section": {
                                                    "query": "assets",
                                                    "boost": 0.5
                                                }
                                            }
                                        },
                                        {
                                            "match_phrase": {
                                                "name": {
                                                    "query": "assets",
                                                    "boost": 0.05
                                                }
                                            }
                                        },
                                        {
                                            "match_phrase": {
                                                "name": {
                                                    "query": "assets",
                                                    "boost": 0.05
                                                }
                                            }
                                        },
                                        {
                                            "match_phrase": {
                                                "name": {
                                                    "query": "assets",
                                                    "boost": 0.05
                                                }
                                            }
                                        }
                                    ]
                                }
                            }, {
                                "bool": {
                                    "should": [
                                        {
                                            "match_phrase": {
                                                "body": {
                                                    "query": "total",
                                                    "boost": 1
                                                }
                                            }
                                        }, {
                                            "match_phrase": {
                                                "section": {
                                                    "query": "total",
                                                    "boost": 0.5
                                                }
                                            }
                                        }, {
                                            "match_phrase": {
                                                "section": {
                                                    "query": "total",
                                                    "boost": 0.5
                                                }
                                            }
                                        },
                                        {
                                            "match_phrase": {
                                                "name": {
                                                    "query": "total",
                                                    "boost": 0.05
                                                }
                                            }
                                        },
                                        {
                                            "match_phrase": {
                                                "name": {
                                                    "query": "total",
                                                    "boost": 0.05
                                                }
                                            }
                                        },
                                        {
                                            "match_phrase": {
                                                "name": {
                                                    "query": "total",
                                                    "boost": 0.05
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
                "highlight": {
                    "highlight_query": {
                        "bool": {
                            "must": [
                                {
                                    "bool": {
                                        "should": [
                                            {
                                                "match_phrase": {
                                                    "body": {
                                                        "query": "assets",
                                                        "boost": 1
                                                    }
                                                }
                                            }, {
                                                "match_phrase": {
                                                    "section": {
                                                        "query": "assets",
                                                        "boost": 0.5
                                                    }
                                                }
                                            }, {
                                                "match_phrase": {
                                                    "section": {
                                                        "query": "assets",
                                                        "boost": 0.5
                                                    }
                                                }
                                            }, {
                                                "match_phrase": {
                                                    "name": {
                                                        "query": "assets",
                                                        "boost": 0.05
                                                    }
                                                }
                                            }, {
                                                "match_phrase": {
                                                    "name": {
                                                        "query": "assets",
                                                        "boost": 0.05
                                                    }
                                                }
                                            }, {
                                                "match_phrase": {
                                                    "name": {
                                                        "query": "assets",
                                                        "boost": 0.05
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }, {
                                    "bool": {
                                        "should": [
                                            {
                                                "match_phrase": {
                                                    "body": {
                                                        "query": "total",
                                                        "boost": 1
                                                    }
                                                }
                                            },
                                            {
                                                "match_phrase": {
                                                    "section": {
                                                        "query": "total",
                                                        "boost": 0.5
                                                    }
                                                }
                                            },
                                            {
                                                "match_phrase": {
                                                    "section": {
                                                        "query": "total",
                                                        "boost": 0.5
                                                    }
                                                }
                                            },
                                            {
                                                "match_phrase": {
                                                    "name": {
                                                        "query": "total",
                                                        "boost": 0.05
                                                    }
                                                }
                                            },
                                            {
                                                "match_phrase": {
                                                    "name": {
                                                        "query": "total",
                                                        "boost": 0.05
                                                    }
                                                }
                                            },
                                            {
                                                "match_phrase": {
                                                    "name": {
                                                        "query": "total",
                                                        "boost": 0.05
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    },
                    "order": "score",
                    "fields": {
                        "body": {
                            "number_of_fragments": 20
                        },
                        "section": {
                            "number_of_fragments": 0
                        },
                        "name": {
                            "number_of_fragments": 0
                        }
                    }
                }
            }
        )
        manager = FileManager("this is a placeholder")
        output = manager._build_query(fake_keywords)

        # ASSERTIONS
        # (c)
        self.assertEqual(expected, output)


if __name__ == '__main__':
    unittest.main()
