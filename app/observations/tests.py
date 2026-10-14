from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .rag import RagConfigurationError, create_chunks, load_pdf_pages


class LandslideObservationApiTests(APITestCase):
    url = '/api/observations/'
    valid_observation = {
        'location_id': 1,
        'max_temp_c': 27.5,
        'humidity_pct': 84.0,
        'wind_speed_kmh': 12.0,
        'rainfall_mm': 35.5,
        'slope_angle_deg': 32,
        'vegetation_cover': 'Medium',
    }

    def test_get_returns_empty_array_when_no_observations_exist(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_post_creates_observation_and_get_returns_it(self):
        with patch(
            'observations.views.predict_landslide',
            return_value={
                'landslide_prediction': 'Yes',
                'landslide_probability': 0.75,
            },
        ):
            first_response = self.client.post(
                self.url,
                self.valid_observation,
                format='json',
            )
        with patch(
            'observations.views.predict_landslide',
            return_value={
                'landslide_prediction': 'No',
                'landslide_probability': 0.25,
            },
        ):
            second_response = self.client.post(
                self.url,
                {**self.valid_observation, 'location_id': 2},
                format='json',
            )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first_response.data['landslide_prediction'], 'Yes')
        self.assertEqual(first_response.data['landslide_probability'], 0.75)
        self.assertIsNone(first_response.data['landslide_observed'])
        self.assertIn('id', first_response.data)
        self.assertIn('created_at', first_response.data)

        list_response = self.client.get(self.url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 2)
        self.assertEqual(
            [record['id'] for record in list_response.data],
            [second_response.data['id'], first_response.data['id']],
        )

    def test_post_uses_the_saved_model_to_predict_landslide(self):
        response = self.client.post(
            self.url,
            self.valid_observation,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(response.data['landslide_prediction'], ('Yes', 'No'))
        self.assertGreaterEqual(response.data['landslide_probability'], 0)
        self.assertLessEqual(response.data['landslide_probability'], 1)

    @patch(
        'observations.views.predict_landslide',
        return_value={
            'landslide_prediction': 'No',
            'landslide_probability': 0.2,
        },
    )
    def test_put_updates_observation_and_recalculates_prediction(self, predict):
        created = self.client.post(self.url, self.valid_observation, format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        updated_data = {**self.valid_observation, 'rainfall_mm': 70}
        response = self.client.put(
            f'{self.url}{created.data["id"]}/',
            updated_data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rainfall_mm'], 70)
        self.assertEqual(response.data['landslide_prediction'], 'No')
        self.assertEqual(response.data['landslide_probability'], 0.2)
        predict.assert_called()

    @patch(
        'observations.views.predict_landslide',
        return_value={
            'landslide_prediction': 'No',
            'landslide_probability': 0.3,
        },
    )
    def test_patch_updates_observation(self, predict):
        created = self.client.post(self.url, self.valid_observation, format='json')
        response = self.client.patch(
            f'{self.url}{created.data["id"]}/',
            {'rainfall_mm': 55},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rainfall_mm'], 55)
        self.assertEqual(response.data['landslide_prediction'], 'No')
        predict.assert_called()

    @patch(
        'observations.views.predict_landslide',
        return_value={
            'landslide_prediction': 'No',
            'landslide_probability': 0.3,
        },
    )
    def test_delete_removes_observation(self, _predict):
        created = self.client.post(self.url, self.valid_observation, format='json')
        response = self.client.delete(f'{self.url}{created.data["id"]}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get(self.url).data, [])

    @patch(
        'observations.views.predict_landslide',
        return_value={
            'landslide_prediction': 'No',
            'landslide_probability': 0.3,
        },
    )
    def test_prediction_fields_cannot_be_set_by_the_client(self, _predict):
        response = self.client.post(
            self.url,
            {
                **self.valid_observation,
                'landslide_observed': 'Yes',
                'landslide_prediction': 'Yes',
                'landslide_probability': 1,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['landslide_prediction'], 'No')
        self.assertEqual(response.data['landslide_probability'], 0.3)

    @patch(
        'observations.views.predict_landslide',
        side_effect=ImproperlyConfigured('model missing'),
    )
    def test_create_returns_service_unavailable_when_model_is_missing(self, _predict):
        response = self.client.post(self.url, self.valid_observation, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @patch(
        'observations.views.predict_landslide',
        return_value={
            'landslide_prediction': 'No',
            'landslide_probability': 0.3,
        },
    )
    def test_post_rejects_invalid_choice(self, _predict):
        invalid_observation = {
            **self.valid_observation,
            'vegetation_cover': 'Unknown',
        }

        response = self.client.post(
            self.url,
            invalid_observation,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('vegetation_cover', response.data)


class SafetyAssistantApiTests(APITestCase):
    url = '/api/safety-assistant/'

    @patch(
        'observations.views.ask_rag',
        return_value={
            'answer': 'Move away from the path of a landslide [page 1].',
            'sources': [
                {'page': 1, 'score': 0.83, 'text': 'Move away from the path.'}
            ],
        },
    )
    def test_post_returns_document_answer_and_sources(self, ask_rag):
        response = self.client.post(
            self.url,
            {'question': 'What should I do during a landslide?'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['answer'], 'Move away from the path of a landslide [page 1].')
        self.assertEqual(response.data['sources'][0]['page'], 1)
        ask_rag.assert_called_once_with('What should I do during a landslide?')

    @patch('observations.views.ask_rag')
    def test_post_rejects_short_question(self, ask_rag):
        response = self.client.post(
            self.url,
            {'question': '  '},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        ask_rag.assert_not_called()

    @patch(
        'observations.views.ask_rag',
        side_effect=RagConfigurationError('Set PINECONE_API_KEY in .env.'),
    )
    def test_post_reports_missing_pinecone_configuration(self, _ask_rag):
        response = self.client.post(
            self.url,
            {'question': 'How should I stay safe?'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class RagDocumentTests(SimpleTestCase):
    def test_create_chunks_keeps_overlap_between_chunks(self):
        chunks = create_chunks('one two three four five six', chunk_size=4, overlap=2)

        self.assertEqual(
            chunks,
            ['one two three four', 'three four five six'],
        )

    def test_create_chunks_rejects_invalid_overlap(self):
        with self.assertRaises(ValueError):
            create_chunks('some words', chunk_size=4, overlap=4)

    def test_load_pdf_pages_reads_project_safety_guide(self):
        pages = load_pdf_pages()

        self.assertTrue(pages)
        self.assertIn('LANDSLIDE', pages[0][1])
        self.assertIn('-', pages[0][1])
