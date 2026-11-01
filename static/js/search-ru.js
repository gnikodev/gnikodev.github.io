// Both Zola's Russian index and lunr-languages' Russian query trimmer discard
// Latin terms. Rebuild this small blog's index lazily from its stored documents
// with a mixed-script trimmer so "Obsidian" and "Rust" remain searchable.
if (document.documentElement.lang === 'ru') {
    const trimmer = lunr.trimmerSupport.generateTrimmer(
        lunr.ru.wordCharacters + 'A-Za-z0-9'
    );
    // Replace the registered function before the lazily loaded index uses it.
    trimmer.label = 'trimmer-ru';
    lunr.Pipeline.registeredFunctions['trimmer-ru'] = trimmer;
    lunr.ru.trimmer = trimmer;

    const loadIndex = lunr.Index.load;
    lunr.Index.load = function (data) {
        if (data.lang !== 'Russian') {
            return loadIndex.call(this, data);
        }
        return lunr(function () {
            this.setRef(data.ref);
            data.fields.forEach((field) => this.addField(field));
            this.use(lunr.ru);
            Object.values(data.documentStore.docs).forEach((doc) => this.addDoc(doc));
        });
    };
}
