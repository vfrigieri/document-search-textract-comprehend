import boto3

comprehend = boto3.client('comprehend')
translate = boto3.client('translate')


class DocumentAnalyzer():
    def _split_text(texto):
        # constantes
        split_char = "\n"
        qte_chars = 10

        splited = texto.split(split_char)
        final_result = []
        result = []
        for linha in splited:
            print("linha: ", len(linha))
            current = len(linha)
            
            if (len(result) == 0):
                print("primeira linha")
                result.append(linha)
            else:
                index = len(result) - 1
                result_current = len(result[index])
                if result_current + current < qte_chars:
                    print("cabe")
                    result[index] = result[index] + linha
                else:
                    print("cabe nao")
                    result.append(linha)

        print('coube em {} linhas'.format(len(result)))
        return result

    def _call_comprehend(texto):
        final_doc = self._split_multiple_array_to_comprehend(texto)
        result = []

        for item in final_doc:
            print('CALL COMPREHEND - chamando: ', final_doc)
            retorno = comprehend.batch_detect_entities(LanguageCode="pt", TextList=item)
            for item in retorno['ResultList']:
                if not item['Entities']:
                    print('no entities found for line ', item)
                for entity in item['Entities']:
                    result.append({
                        "Score": entity['Score'],
                        "Type": entity['Type'],
                        "Text": entity['Text']
                    })
        return result

    def _split_multiple_array_to_comprehend(texto):
        linhas = self._split_text(texto)
        final_doc = []
        line_count = 1
        part = []
        for item in linhas:
            part.append(item)
            if len(final_doc) == 0:
                final_doc.append(part)

            if (line_count > 24):
                part = []
                final_doc.append(part)
                line_count = 0
            line_count = line_count + 1
        return final_doc

    def extract_entities(self, pages):
        """ extract entities from pages with Comprehend """

        selected_entity_types = ["ORGANIZATION", "PERSON", "LOCATION", "DATE"]

        final_entities = []
        for page in pages:
            #text = self.__get_clean_text_in_supported_language(page['Content'])

            text = page['Content']

            final_entities = self._call_comprehend(text)
            # detected_entities = comprehend.detect_entities(
            #     Text=text,
            #     LanguageCode="en"
            # )

            # uncomment to see output of comprehend
            # print(detected_entities)

            # selected_entities = [x for x in detected_entities['Entities']
            #                      if x['Score'] > 0.9 and
            #                      x['Type'] in selected_entity_types]

            # for selected_entity in selected_entities:
            #     clean_entity = {key: selected_entity[key]
            #                     for key in ["Text", "Type"]}
            #     if clean_entity not in final_entities:
            #         final_entities.append(clean_entity)

        return final_entities

    def __get_clean_text_in_supported_language(self, inputText):
        """ Prepare text for Comprehend:
        reduce the size of the text to 5000 bytes
        and translate it in english if not in supported language """

        # max size for Comprehend: 5000 bytes
        text = inputText[:5000]

        languages = comprehend.detect_dominant_language(
            Text=text
        )
        dominant_languages = sorted(languages['Languages'],
                                    key=lambda k: k['LanguageCode'])
        dominant_language = dominant_languages[0]['LanguageCode']

        if dominant_language not in ['en', 'es', 'fr', 'de', 'it', 'pt']:
            translation = translate.translate_text(
                Text=text,
                SourceLanguageCode=dominant_language,
                TargetLanguageCode="en"
            )
            text = translation['TranslatedText']

        return text[:5000]