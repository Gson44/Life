document.addEventListener('DOMContentLoaded', function () {

    // Extracting habit data from the HTML
    const habitDataElement = document.getElementById('habit');
    const habitDataRaw = habitDataElement.getAttribute('data-habit_data');
    const habitData = JSON.parse(habitDataRaw);

    // Filter data for the current month
    const currentMonth = new Date().getMonth();
    const filteredData = habitData.filter(entry => {
        const entryDate = new Date(entry[4]);
        return entryDate.getMonth() === currentMonth;
    });

    const tableContainer = document.querySelector('.tracker-table');

    for (let day = 1; day <= 31; day++) {
        const container = document.createElement('div');
        container.className = 'day-container';

        const dayLabel = document.createElement('div');
        dayLabel.className = 'day-label';
        dayLabel.textContent = day;
        container.appendChild(dayLabel);

        const dayData = filteredData.find(entry => {
            const entryDate = new Date(entry[4]);
            return entryDate.getDate() === day;
        });

        for (let habitNum = 0; habitNum < 3; habitNum++) {
            const habitCell = document.createElement('div');
            habitCell.className = 'habit-cell';

            if (dayData && dayData[habitNum + 1] === 1) {
                habitCell.classList.add('completed');
            } else {
                habitCell.classList.add('not-completed');
            }

            container.appendChild(habitCell);
        }

        tableContainer.appendChild(container);
    }

    // For displaying today's date in the "Today: " section
    const today = new Date();
    const dateString = today.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    document.getElementById('time').textContent = dateString;

});

