import {Chart} from "chart.js";

const value = [10, 8, 12, 3, 4, 10]

const ctx = document.getElementById('cryptoChart').getContext('2d');

const myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['6m', '5m', '4m', '3m', '2m', '1m'],
        datasets: [{
            label: 'Value over time',
            data: value,
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            fill: true
        }]
    },
    options: {}
});