function formatPrice(price) {
    return new Intl.NumberFormat('en-IN').format(price);
}

function createRecommendationCard(product) {
    return `
        <div class="recommendation-card">
            <img src="${product.image}" alt="${product.title}">
            <h4>${product.title}</h4>
            <a href="${product.url}" target="_blank" class="view-button">View Product</a>
        </div>
    `;
}

async function scrapeProduct() {
    const productUrl = document.getElementById('productUrl').value.trim();
    if (!productUrl) {
        showError('Please enter a product URL');
        return;
    }

    if (!productUrl.includes('amazon.')) {
        showError('Please enter a valid Amazon product URL');
        return;
    }

    // Show loader and hide other elements
    document.getElementById('loader').style.display = 'block';
    document.getElementById('productCard').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';

    try {
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: productUrl })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch product details');
        }

        const data = await response.json();

        if (data.title && data.price) {
            // Update product card
            document.getElementById('productTitle').textContent = data.title;
            document.getElementById('productPrice').textContent = formatPrice(data.price);
            document.getElementById('productLink').href = data.product_url;
            
            // Set product image
            if (data.image_url) {
                document.getElementById('productImage').src = data.image_url;
            }

            // Set rating if available
            if (data.rating) {
                document.getElementById('productRating').textContent = data.rating;
            }

            // Set description if available
            if (data.description) {
                document.getElementById('productDescription').textContent = data.description;
            }

            // Set features if available
            if (data.features && data.features.length > 0) {
                const featuresList = document.getElementById('productFeatures');
                featuresList.innerHTML = data.features.map(feature => `<li>${feature}</li>`).join('');
            }

            // Set recommended products if available
            if (data.recommended_products && data.recommended_products.length > 0) {
                const recommendationsContainer = document.getElementById('recommendedProducts');
                recommendationsContainer.innerHTML = data.recommended_products
                    .map(createRecommendationCard)
                    .join('');
            }
            
            // Show product card
            document.getElementById('productCard').style.display = 'block';
        } else {
            document.getElementById('errorMessage').style.display = 'block';
        }
    } catch (error) {
        showError(error.message || 'Could not fetch product details. Please try again.');
    } finally {
        document.getElementById('loader').style.display = 'none';
    }
}

function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    document.getElementById('productCard').style.display = 'none';
    document.getElementById('loader').style.display = 'none';
}
