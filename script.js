document.addEventListener('DOMContentLoaded', function () {
    const searchBox = document.getElementById('searchBox');

    const suggestionsBox = document.createElement('div');
    suggestionsBox.id = 'suggestionsBox';
    suggestionsBox.style.position = 'absolute';
    suggestionsBox.style.background = 'white';
    suggestionsBox.style.border = '1px solid #ccc';
    suggestionsBox.style.width = '80%';
    suggestionsBox.style.maxHeight = '200px';
    suggestionsBox.style.overflowY = 'auto';
    suggestionsBox.style.zIndex = '999';
    suggestionsBox.style.display = 'none';
    searchBox.parentNode.appendChild(suggestionsBox);

    // Define all product names and their links
    const products = [
        { name: 'Mixture', link: '/snacks#mixture' },
        { name: 'Murukku', link: '/snacks#murukku' },
        { name: 'Banana Chips', link: '/snacks#banana' },
        { name: 'Tomato Pickle', link: '/veg_pickles#tomato' },
        { name: 'Amla Pickle', link: '/veg_pickles#amla' },
        { name: 'Mango Pickle', link: '/veg_pickles#mango' },
        { name: 'Chicken Pickle', link: '/non_veg_pickles#chicken' },
        { name: 'Fish Pickle', link: '/non_veg_pickles#fish' }
    ];

    searchBox.addEventListener('input', function () {
        const query = searchBox.value.toLowerCase().trim();
        suggestionsBox.innerHTML = '';
        if (query === '') {
            suggestionsBox.style.display = 'none';
            return;
        }

        const matched = products.filter(p => p.name.toLowerCase().includes(query));
        if (matched.length === 0) {
            suggestionsBox.style.display = 'none';
            return;
        }

        matched.forEach(item => {
            const div = document.createElement('div');
            div.textContent = item.name;
            div.style.padding = '10px';
            div.style.cursor = 'pointer';
            div.addEventListener('click', () => {
                window.location.href = item.link;
            });
            suggestionsBox.appendChild(div);
        });

        suggestionsBox.style.display = 'block';
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', function (e) {
        if (!suggestionsBox.contains(e.target) && e.target !== searchBox) {
            suggestionsBox.style.display = 'none';
        }
    });
});