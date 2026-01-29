from caex2.extractor import extract_episode

TEST_EPISODE_FILEPATH = './test_episode.md'


def test_extractor():
    with open(TEST_EPISODE_FILEPATH) as fin:
        episode_lines = fin.readlines()
    challenges = extract_episode(episode_lines)
    assert len(challenges) == 5
    assert challenges[0].startswith('\n## Pairplot')
