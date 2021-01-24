from tenseflow import change_to_third as third

INPUT = ["""The elevator stops so abruptly that I am literally thrown to the ceiling, then fall back down.""",
		"""That's a lot less fun than I used to imagine it would be, when I took elevators as a kid.""",
		"""I get up, wincing with pain from my left wrist. """,
		"""I've dropped the heart.""",
		"""It's in the corner, broken in two, so I pick up one half in each hand and hope fervently that it still works.""",
		"""Whatever it is, or whatever working means."""]

OUTPUT = ["""The elevator stops so abruptly that he is literally thrown to the ceiling, then fall back down.""",
		"""That's a lot less fun than he used to imagine it would be, when he took elevators as a kid.""",
		"""He gets up, wincing with pain from his left wrist.""",
		"""He's dropped the heart.""",
		"""It's in the corner, broken in two, so he picks up one half in each hand and hopes fervently that it still works.""",
		"""Whatever it is, or whatever working means."""]


def test_change_to_third():
    for i in range(0, len(INPUT)):
    	assert third(INPUT[i], "he") == OUTPUT[i]

def test_quotes():
	assert third("""I glared at Bob. "Don't push me," I snarled.""", "he") == """He glared at Bob. "Don't push me," he snarled."""