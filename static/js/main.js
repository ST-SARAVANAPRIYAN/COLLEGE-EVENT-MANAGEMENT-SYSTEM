/**
 * College Event Management System (CEMS) Main JavaScript
 * Handles shared functionality across pages
 */

// Fetch events from the API or use fallback data if the API is unavailable
async function fetchEvents() {
  try {
    const response = await fetch('/api/events');
    if (response.ok) {
      return await response.json();
    }
    console.warn('API unavailable, using fallback event data');
    return fallbackEvents;
  } catch (error) {
    console.warn('Error fetching events:', error);
    return fallbackEvents;
  }
}

// Render event cards for the homepage
function renderEventCards() {
  const eventList = document.getElementById("event-list");
  if (!eventList) return;
  
  // Show loading spinner
  eventList.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading events...</span>
      </div>
    </div>
  `;
  
  fetchEvents().then(events => {
    if (events.length === 0) {
      eventList.innerHTML = '<div class="alert alert-info">No events available at this time.</div>';
      return;
    }
    
    let cardsHtml = '<div class="row g-4">';
    
    // Limit to 6 events on homepage
    const displayEvents = events.slice(0, 6);
    
    displayEvents.forEach(event => {
      cardsHtml += `
        <div class="col-md-4 d-flex align-items-stretch">
          <div class="card shadow-sm ${event.tag === 'technical' ? 'border-primary technical-card' : 'border-warning non-technical-card'}" style="border-radius:1rem; cursor:pointer; width: 100%;">
            ${event.image ? 
              `<img src='${event.image}' class='card-img-top' alt='${event.name}' style='height:180px;object-fit:cover;border-radius:1rem 1rem 0 0;'>` : 
              `<div class='event-gradient d-flex align-items-center justify-content-center' style='height:180px;border-radius:1rem 1rem 0 0;background:${event.tag === 'technical' ? 'linear-gradient(135deg, #6e8efb, #a777e3)' : 'linear-gradient(135deg, #f6d365, #fda085)'};'>
                <h4 class="text-white text-center px-2">${event.name}</h4>
              </div>`
            }
            <div class="card-body d-flex flex-column">
              <h5 class="card-title">${event.name}</h5>
              <p class="card-text flex-grow-1">${event.description ? (event.description.length > 70 ? event.description.substring(0, 70) + '...' : event.description) : 'No description available.'}</p>
              <div class="mt-2">
                <span class="badge ${event.tag === 'technical' ? 'bg-primary' : 'bg-warning text-dark'}">${event.tag === 'technical' ? 'Technical' : 'Non-Technical'}</span>
                <p class="card-text mt-2"><small class="text-muted">${event.date}</small></p>
                <button class="btn btn-outline-info btn-sm mt-1" onclick="showEventDetail(${event.id})">View Details</button>
                ${event.has_exploration ? 
                  `<a href="/event_exploration/${event.id}" target="_blank" class="btn btn-outline-primary btn-sm mt-1 ms-1">Explore</a>` : 
                  ''
                }
              </div>
            </div>
          </div>
        </div>
      `;
    });
    
    cardsHtml += '</div>';
    eventList.innerHTML = cardsHtml;
  });
}

// Create a Bootstrap modal for event details
function createEventModal() {
  if (document.getElementById('eventDetailModal')) return;
  
  const modalHtml = `
    <div class="modal fade" id="eventDetailModal" tabindex="-1" aria-labelledby="eventDetailModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="eventDetailModalLabel">Event Details</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" id="eventDetailBody">
            <div class="text-center">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <a href="/login" class="btn btn-primary" id="loginToRegisterBtn">Login to Register</a>
          </div>
        </div>
      </div>
    </div>
  `;
  
  document.body.insertAdjacentHTML('beforeend', modalHtml);
}

// Show event details in a modal
async function showEventDetail(eventId) {
  createEventModal();
  const modal = new bootstrap.Modal(document.getElementById('eventDetailModal'));
  modal.show();
  
  try {
    const response = await fetch(`/api/events/${eventId}`);
    if (!response.ok) throw new Error('Failed to fetch event details');
    
    const event = await response.json();
    
    const explorationButton = event.has_exploration 
      ? `<a href="/event_exploration/${event.id}" target="_blank" class="btn btn-primary btn-sm me-2">Explore This Event</a>` 
      : '';

    const body = `
      <div class="container-fluid">
        <div class="row">
          <div class="col-md-6">
            ${event.image ? 
              `<img src='${event.image}' class='img-fluid rounded mb-3' alt='${event.name}'>` : 
              `<div class='event-gradient d-flex align-items-center justify-content-center mb-3' style='height:200px;background:${event.tag === 'technical' ? 'linear-gradient(135deg, #6e8efb, #a777e3)' : 'linear-gradient(135deg, #f6d365, #fda085)'};border-radius:0.5rem;'>
                <h3 class="text-white text-center px-3">${event.name}</h3>
              </div>`
            }
            ${event.video ? 
              `<div class="ratio ratio-16x9 mb-3">
                <video controls>
                  <source src="${event.video}" type="video/mp4">
                  Your browser does not support the video tag.
                </video>
              </div>` : 
              ''
            }
          </div>
          <div class="col-md-6">
            <h4>${event.name}</h4>
            <p><strong>Date:</strong> ${event.date}</p>
            <p>${event.description || 'No description available.'}</p>
            <span class="badge ${event.tag === 'technical' ? 'bg-primary' : 'bg-warning text-dark'}">${event.tag === 'technical' ? 'Technical' : 'Non-Technical'}</span>
            ${event.fee > 0 ? `<div class="mt-2"><strong>Registration Fee:</strong> ₹${event.fee}</div>` : ''}
            <div class="mt-3">
              ${event.brochure ? 
                `<a class="btn btn-outline-secondary btn-sm me-2" href="${event.brochure}" download>Download Brochure</a>` : 
                ''
              }
              ${explorationButton}
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.getElementById('eventDetailBody').innerHTML = body;
    
  } catch (error) {
    console.error('Error fetching event details:', error);
    document.getElementById('eventDetailBody').innerHTML = `
      <div class="alert alert-danger">
        Failed to load event details. Please try again later.
      </div>
    `;
  }
}

// Fallback event data if API is unavailable
const fallbackEvents = [
  {
    id: 1,
    name: "Tech Hackathon 2025",
    date: "2025-05-10",
    description: "A 24-hour coding marathon for tech enthusiasts.",
    tag: "technical",
    image: "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=600&q=80",
    video: null,
    brochure: null,
    has_exploration: true,
    fee: 200
  },
  {
    id: 2,
    name: "Cultural Fest",
    date: "2025-05-15",
    description: "A celebration of art, music, and dance.",
    tag: "non-technical",
    image: "https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=600&q=80",
    video: null,
    brochure: null,
    has_exploration: false,
    fee: 100
  },
  {
    id: 3,
    name: "Robotics Workshop",
    date: "2025-05-20",
    description: "Hands-on robotics workshop for beginners.",
    tag: "technical",
    image: "https://images.unsplash.com/photo-1535378620166-273708d44e4c?auto=format&fit=crop&w=600&q=80",
    video: null,
    brochure: null,
    has_exploration: false,
    fee: 150
  },
  {
    id: 4,
    name: "Stand-up Comedy Night",
    date: "2025-05-22",
    description: "Laugh out loud with the best campus comedians!",
    tag: "non-technical",
    image: "https://images.unsplash.com/photo-1527224538127-2104bb71c51b?auto=format&fit=crop&w=600&q=80",
    video: null,
    brochure: null,
    has_exploration: false,
    fee: 50
  }
];

// Initialize the page
document.addEventListener("DOMContentLoaded", function() {
  // Render event cards on homepage
  if (document.getElementById('event-list')) {
    renderEventCards();
  }
});
