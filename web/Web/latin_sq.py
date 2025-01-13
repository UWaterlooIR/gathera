import random
from web.core.models import Session
from web.users.models import User
from web.topic.models import Topic
import string

SEED = 2025



class TopicTypeCustom:
    def __init__(self, seed_query, description=None, narrative=None, label=None):
        self.seed_query = seed_query
        self.description = description
        self.narrative = narrative
        self.label = label

    def add_label(self, label):
        assert label in ['a', 'b', 'c', 'd', 'e']
        self.label = label

    def __str__(self):
        return f'{self.seed_query} - {self.label}'


class SessionType:
    def __init__(self, name, integrated_cal, nudge, search_disabled, label=None):
        self.name = name
        self.integrated_cal = integrated_cal
        self.nudge = nudge
        self.search_disabled = search_disabled
        self.label = label

    def add_label(self, label):
        assert label in ['A', 'B', 'C', 'D', 'E']
        self.label = label

    def __str__(self):
        return f'{self.name} - {self.label}'




treatments_base = [
    ['A', 'B', 'C', 'D', 'E'],
    ['B', 'C', 'D', 'E', 'A'],
    ['C', 'D', 'E', 'A', 'B'],
    ['D', 'E', 'A', 'B', 'C'],
    ['E', 'A', 'B', 'C', 'D'],
]

topics_base = [
    ['a', 'b', 'c', 'd', 'e'],
    ['c', 'd', 'e', 'a', 'b'],
    ['e', 'a', 'b', 'c', 'd'],
    ['b', 'c', 'd', 'e', 'a'],
    ['d', 'e', 'a', 'b', 'c'],
]

def print_latin_sq(sq):
    for i in sq:
        print(i)
    print('------------------------------')


def shuffle_rows(sq):
    random.seed(SEED)
    random.shuffle(sq)
    return sq


def shuffle_columns(latin_square):
    random.seed(SEED)
    n = len(latin_square)
    column_indices = list(range(n))
    random.shuffle(column_indices)
    shuffled_square = []
    for row in latin_square:
        shuffled_row = [row[i] for i in column_indices]
        shuffled_square.append(shuffled_row)
    return shuffled_square

def shuffle_rows_and_columns(latin_square):
    random.seed(SEED)
    return shuffle_columns(shuffle_rows(latin_square))

def superimposed_latin_square(treatments, topics):
    random.seed(SEED)
    super_imposed_square = []
    for i in range(len(treatments)):
        super_imposed_square.append([])
        for j in range(len(topics)):
            super_imposed_square[i].append((treatments[i][j], topics[i][j]))
    return super_imposed_square


def test_latin_sq_correct(latin_sq):
    for row in latin_sq:
        if len(set(row)) != len(row):
            return False
    for i in range(len(latin_sq)):
        column = [latin_sq[j][i] for j in range(len(latin_sq))]
        if len(set(column)) != len(column):
            return False
    return True




def map_labels_to_treatments_and_topics(session_types, topics_list):
    session_mapping = {}
    for i in range(len(session_types)):
        session_mapping[session_types[i].label] = session_types[i]
    topic_mapping = {}
    for i in range(len(topics_list)):
        topic_mapping[topics_list[i].label] = topics_list[i]
    return session_mapping, topic_mapping



def assign_random_labels_to_topics_and_sessions(sessions, topics, ):
    random.seed(SEED)
    topics_choices = ['a', 'b', 'c', 'd', 'e']
    sessions_choices = ['A', 'B', 'C', 'D', 'E']
    for i in range(len(topics)):
        topics[i].add_label(random.choice(topics_choices))
        topics_choices.remove(topics[i].label)
    for i in range(len(sessions)):
        sessions[i].add_label(random.choice(sessions_choices))
        sessions_choices.remove(sessions[i].label)
    return sessions, topics

def add_topics_and_sessions_to_latin_square(session_mapping, topic_mapping, latin_square):
    for i in range(len(latin_square)):
        for j in range(len(latin_square[i])):
            latin_square[i][j] = (session_mapping[latin_square[i][j][0]], topic_mapping[latin_square[i][j][1]])
    return latin_square


def create_final_latin_square(treatments, topics, base_latin_treatments, base_latin_topics):
    latin_sq = superimposed_latin_square(base_latin_treatments, base_latin_topics)
    latin_sq = shuffle_rows_and_columns(latin_sq)
    assert test_latin_sq_correct(latin_sq)
    sessions, topics = assign_random_labels_to_topics_and_sessions(treatments, topics)
    session_mapping, topic_mapping = map_labels_to_treatments_and_topics(sessions, topics)
    final_latin_sq = add_topics_and_sessions_to_latin_square(session_mapping, topic_mapping, latin_sq)
    assert test_latin_sq_correct(final_latin_sq)
    return final_latin_sq


def create_5_sessions_and_a_random_user(config_list):
    random.seed(None)
    random_username = f'experiment_user_{random.randint(1000, 9999)}'
    random_password = (f'{random.randint(1000, 9999)}_'
                       f'{random.choice(string.ascii_lowercase)}_{random.choice(string.ascii_uppercase)}')
    random_user = User.objects.create_user(random_username,
                                                 '{}@crazymail.com'.format(random_username),
                                                 random_password)
    random_user.save()
    print(random_username,  random_password)
    for i, config in enumerate(config_list):
        session_to_create = config[0]
        query = config[1]
        topic = Topic(
            title=f'{query.seed_query}',
            seed_query=f'{query.seed_query}+{query.description}+{query.narrative}',
            description=query.description,
            narrative=query.narrative,
        )
        topic.save()
        session = Session.objects.create(
            username=random_user,
            integrated_cal=session_to_create.integrated_cal,
            nudge_to_cal=session_to_create.nudge,
            disable_search=session_to_create.search_disabled,
            topic=topic,
            session_order=i,
            max_number_of_judgments=0,
            show_full_document_content=True,
            strategy='para',
            show_debugging_content=0,
            max_time=20,
        )
        session.save()
    current_session_to_start = Session.objects.filter(username=random_user).order_by('session_order').first()
    random_user.current_session = current_session_to_start
    random_user.save()
    current_session_to_start.begin_session_in_cal()



SESSION_TYPES = [
        SessionType('integrated-cal', True, False, False),
        SessionType('cal-only', False, False, True),
        SessionType('integrated-cal-with-nudge', True, True, False),
        SessionType('cal-with-nudge', False, True, False),
        SessionType('base', False, False, False)
]

TOPICS = [
    TopicTypeCustom(
        'tropical storms',
        'What tropical storms (hurricanes and typhoons) have '
        'caused significant property damage and loss of life?',
        'The date of the storm, the area affected, and the extent of'
        ' damage/casualties are all of interest.  Documents that describe the'
        ' damage caused by a tropical storm as "slight", "limited", or "small"'
        ' are not relevant.',
        1,
    ),
    TopicTypeCustom(
        'steel production',
        'What are new methods of producing steel?',
        'Relevant documents will discuss the processes adapted '
        'by entrepreneurs who have organized so-called "minimills" '
        'and are producing steel by methods which differ from the '
        'old blast furnace method of production.  Documents that '
        'identify the new companies, the problems they have have '
        'encountered, and/or their successes or failures in the '
        'national and international markets are also relevant.',
        2,
    ),
    TopicTypeCustom(
        'UV damage eyes',
        'Find documents that discuss the damage ultraviolet (UV) light from the sun '
        'can do to eyes.',
        'A relevant document will discuss diseases that result '
        'from exposure of the eyes to UV light, treatments for the damage, '
        'and/or education programs that help prevent damage.  Documents discussing '
        'treatment methods for cataracts and ocular melanoma are relevant even when '
        'a specific cause is not mentioned. However, documents that discuss radiation '
        'damage from nuclear sources or lasers are not relevant.'),
    TopicTypeCustom(
        'art, stolen, forged',
        'What incidents have there been of stolen or forged art?',
        'Instances of stolen or forged art in any media are relevant.'
        ' Stolen mass-produced things, even though they might be decorative,'
        ' are not relevant (unless they are mass-produced art reproductions).'
        ' Pirated software, music, movies, etc. are not relevant.'),
    TopicTypeCustom(
        'robotic technology',
        'What are the latest developments in robotic technology?',
        'A relevant document will contain information on current applications of '
        'robotic technology. Discussions of robotics research or simulations of '
        'robots are not relevant.'
    )
]


final = create_final_latin_square(SESSION_TYPES, TOPICS, treatments_base, topics_base)

create_5_sessions_and_a_random_user(final[0])
