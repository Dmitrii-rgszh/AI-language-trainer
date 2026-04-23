import { routes } from "../constants/routes";

type LensRoute =
  | typeof routes.grammar
  | typeof routes.vocabulary
  | typeof routes.speaking
  | typeof routes.pronunciation
  | typeof routes.writing
  | typeof routes.reading
  | typeof routes.listening
  | typeof routes.progress;

export type EnglishRelationshipLens = {
  title: string;
  principle: string;
  successLabel: string;
  successSummary: string;
  pressureRelease: string;
};

export function describeEnglishRelationshipLens(
  route: LensRoute,
  tr: (value: string) => string,
): EnglishRelationshipLens {
  switch (route) {
    case routes.grammar:
      return {
        title: tr("Grammar through living language"),
        principle: tr("Grammar is not a purity test here. It is a tool for saying something more clearly, lightly, and confidently."),
        successLabel: tr("Success now"),
        successSummary: tr("One usable pattern that you can carry into speaking or writing is more valuable than covering every rule."),
        pressureRelease: tr("Mistakes are signals for the next route step, not proof that you are bad at English."),
      };
    case routes.vocabulary:
      return {
        title: tr("Vocabulary through personal meaning"),
        principle: tr("Vocabulary should grow from real phrases, real context, and real reuse, not from detached word lists."),
        successLabel: tr("Success now"),
        successSummary: tr("If one phrase comes back into your writing or speaking, the route is working even without a huge word count jump."),
        pressureRelease: tr("You do not have to memorize everything. The route will bring useful language back when it becomes timely."),
      };
    case routes.speaking:
      return {
        title: tr("Speaking through courage, not performance"),
        principle: tr("Speaking is a place to hear your own English alive, not to prove flawless correctness."),
        successLabel: tr("Success now"),
        successSummary: tr("An honest, usable response with some friction is still strong progress if it increases spontaneity and contact."),
        pressureRelease: tr("The point is not perfect grammar. The point is to keep your voice available and less afraid of being heard."),
      };
    case routes.pronunciation:
      return {
        title: tr("Pronunciation through clarity"),
        principle: tr("Pronunciation is here to make your voice easier, clearer, and more connected, not to chase an artificial perfect accent."),
        successLabel: tr("Success now"),
        successSummary: tr("If one phrase becomes easier to say and easier to trust, that matters more than a sterile score jump."),
        pressureRelease: tr("You are training comfort and intelligibility, not auditioning for perfection."),
      };
    case routes.writing:
      return {
        title: tr("Writing through expression"),
        principle: tr("Writing should help you express a real thought more cleanly and naturally, not freeze you into fear of mistakes."),
        successLabel: tr("Success now"),
        successSummary: tr("A clearer second version that still feels like your own voice is better than a polished draft you can no longer own."),
        pressureRelease: tr("Corrections are here to strengthen your message, not to punish the first draft."),
      };
    case routes.reading:
      return {
        title: tr("Reading through interest"),
        principle: tr("Reading should feel like entering living English through meaning and curiosity, not dissecting text under pressure."),
        successLabel: tr("Success now"),
        successSummary: tr("One useful idea or phrase carried into the next response is enough for a reading pass to be successful."),
        pressureRelease: tr("You do not need to catch everything. The route only needs one signal strong enough to reuse."),
      };
    case routes.listening:
      return {
        title: tr("Listening through signal, not panic"),
        principle: tr("Listening should train your ability to catch useful meaning under real conditions, not trigger fear of missing every word."),
        successLabel: tr("Success now"),
        successSummary: tr("If you catch one operational signal and use it in the next response, the listening pass has already done its job."),
        pressureRelease: tr("Not hearing everything is normal. The route cares about usable understanding, not total control."),
      };
    case routes.progress:
      return {
        title: tr("Progress through relationship"),
        principle: tr("Progress should measure not only scores, but also ease, honesty, reuse, and a healthier relationship with English."),
        successLabel: tr("Success now"),
        successSummary: tr("More spontaneity, less fear, and steadier reuse are real progress even before the visible score jumps catch up."),
        pressureRelease: tr("This screen is here to explain direction, not to reduce your learning life to a judgment board."),
      };
    default:
      return {
        title: tr("English relationship lens"),
        principle: tr("This route should help English feel more alive, usable, and less heavy."),
        successLabel: tr("Success now"),
        successSummary: tr("The best next step is the one that increases honest contact with the language."),
        pressureRelease: tr("Perfection is not the job. Staying connected is the job."),
      };
  }
}
