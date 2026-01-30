from .utils import record_session, replay_session
import argparse

parser = argparse.ArgumentParser("Record or replay GUI events")
parser.add_argument("--replay", help="Event type to replay")
parser.add_argument("--file",   help="Events JSON file path", default=None)
args = parser.parse_args()

if args.replay:
    replay_session(args.replay, args.file)
else:
    record_session(args.file)
