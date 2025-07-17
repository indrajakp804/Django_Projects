function initSnowfall(containerId) {
    const container = document.getElementById(containerId);
    const snowflakeCount = 20; // Number of snowflakes

    for (let i = 0; i < snowflakeCount; i++) {
        const snowflake = document.createElement('div');
        snowflake.classList.add('snowflake');

        // Randomize position and animation properties
        snowflake.style.left = Math.random() * 100 + '%'; // Random horizontal position
        snowflake.style.animationDuration = Math.random() * 3 + 2 + 's'; // Random fall speed
        snowflake.style.animationDelay = Math.random() * 5 + 's'; // Staggered start time
        snowflake.style.opacity = Math.random(); // Random opacity

        container.appendChild(snowflake);
    }
}
