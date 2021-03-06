from django.test import Client, TestCase
from django.utils import timezone

from games.models import Card, Chug, Game, GamePlayer, User
from games.utils import get_milliseconds


class GameViewTest(TestCase):
    def setUp(self):
        self.player1 = User.objects.create(username="Player1")
        self.player2 = User.objects.create(username="Player2")
        self.game = Game.objects.create(start_datetime=timezone.now())

        GamePlayer.objects.create(game=self.game, user=self.player1, position=0)
        GamePlayer.objects.create(game=self.game, user=self.player2, position=1)

        delta = 0

        for i, (value, suit) in enumerate(Card.get_ordered_cards_for_players(2)):
            card = Card.objects.create(
                game=self.game,
                index=i,
                value=value,
                suit=suit,
                start_delta_ms=get_milliseconds(
                    timezone.now() - self.game.start_datetime
                )
                + delta,
            )
            if value == 14:
                Chug.objects.create(card=card, duration_ms=12345)

        self.game.end_datetime = timezone.now()
        self.game.save()

        self.client = Client()

    def assert_can_render_pages(self):
        r = self.client.get(f"/games/")
        self.assertEqual(r.status_code, 200)
        r = self.client.get(f"/games/{self.game.id}/")
        self.assertEqual(r.status_code, 200)

    def test_normal_game(self):
        self.assert_can_render_pages()

    def test_live_game(self):
        self.game.end_datetime = None
        self.game.save()
        self.assert_can_render_pages()

    def test_game_without_card_times(self):
        for c in self.game.ordered_cards():
            c.start_delta_ms = None
            c.save()

        self.assert_can_render_pages()

    def test_game_without_start_time_and_card_times(self):
        for c in self.game.ordered_cards():
            c.start_delta_ms = None
            c.save()

        self.game.start_datetime = None
        self.game.save()
        self.assert_can_render_pages()


class StatsViewTest(TestCase):
    def test_with_no_games(self):
        client = Client()
        r = client.get(f"/stats/")
        self.assertEqual(r.status_code, 200)
