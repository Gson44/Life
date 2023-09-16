document.addEventListener('DOMContentLoaded', function () {

    // Extracting habit data from the HTML
    const habitDataElement = document.getElementById('habit');
    const habitDataRaw = habitDataElement.getAttribute('data-habit_data');
    const habitData = JSON.parse(habitDataRaw);
    console.log(habitData)
    // Filter data for the current month
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth();
    console.log(currentDate)
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
            //console.log(entryDate.getDate())
            //console.log(entryDate.getUTCDate())
            //console.log(entryDate.getDate() +1)
            return entryDate.getUTCDate() === day;
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
    const dateString = currentDate.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    document.getElementById('time').textContent = dateString;

});
