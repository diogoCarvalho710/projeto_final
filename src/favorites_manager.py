import streamlit as st
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class FavoritesManager:
    """Manager for handling favorite players"""

    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.favorites_file = Path("data/temp/favorites.json")
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """Ensure data directory exists"""
        self.favorites_file.parent.mkdir(parents=True, exist_ok=True)

    def load_favorites(self) -> Dict:
        """Load favorites from file"""
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Error loading favorites: {str(e)}")
        return {}

    def save_favorites(self, favorites: Dict):
        """Save favorites to file"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving favorites: {str(e)}")
            return False

    def add_to_favorites(self, player_name: str, position: str, reason: str = "",
                         collection: str = "General", priority: str = "Medium") -> bool:
        """Add player to favorites"""
        try:
            favorites = self.load_favorites()

            # Create unique ID
            fav_id = f"{player_name}_{position}".replace(" ", "_")

            # Check if already exists
            if fav_id in favorites:
                return False

            # Get player data
            player_data = self.data_processor.get_player_data(player_name, position)
            if player_data is None:
                return False

            # Create favorite entry
            favorite_entry = {
                'player_name': player_name,
                'position': position,
                'team': player_data.get('Time', 'Unknown'),
                'age': player_data.get('Idade', 'Unknown'),
                'nationality': player_data.get('Nacionalidade', 'Unknown'),
                'reason': reason,
                'collection': collection,
                'priority': priority,
                'status': 'Scouting',
                'added_date': datetime.now().isoformat(),
                'notes': []
            }

            favorites[fav_id] = favorite_entry
            return self.save_favorites(favorites)

        except Exception as e:
            st.error(f"Error adding to favorites: {str(e)}")
            return False

    def remove_from_favorites(self, fav_id: str) -> bool:
        """Remove player from favorites"""
        try:
            favorites = self.load_favorites()
            if fav_id in favorites:
                del favorites[fav_id]
                return self.save_favorites(favorites)
            return False
        except Exception as e:
            st.error(f"Error removing from favorites: {str(e)}")
            return False

    def update_favorite(self, fav_id: str, updates: Dict) -> bool:
        """Update favorite player information"""
        try:
            favorites = self.load_favorites()
            if fav_id in favorites:
                favorites[fav_id].update(updates)
                return self.save_favorites(favorites)
            return False
        except Exception as e:
            st.error(f"Error updating favorite: {str(e)}")
            return False

    def get_favorites_count(self) -> int:
        """Get total number of favorites"""
        favorites = self.load_favorites()
        return len(favorites)

    def show_favorites_ui_updated(self):
        """Show favorites UI (without suggestions tab)"""
        st.subheader("⭐ Favorite Players")

        favorites = self.load_favorites()

        if not favorites:
            st.info("📭 No favorite players yet. Add players from their profile pages!")
            return

        # Filters and controls
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            collections = list(set([fav['collection'] for fav in favorites.values()]))
            selected_collection = st.selectbox(
                "Filter by Collection",
                ["All"] + collections,
                key="favorites_collection_filter"
            )

        with col2:
            priorities = ["All", "High", "Medium", "Low"]
            selected_priority = st.selectbox(
                "Filter by Priority",
                priorities,
                key="favorites_priority_filter"
            )

        with col3:
            statuses = list(set([fav['status'] for fav in favorites.values()]))
            selected_status = st.selectbox(
                "Filter by Status",
                ["All"] + statuses,
                key="favorites_status_filter"
            )

        with col4:
            positions = list(set([fav['position'] for fav in favorites.values()]))
            selected_position = st.selectbox(
                "Filter by Position",
                ["All"] + positions,
                key="favorites_position_filter"
            )

        # Apply filters
        filtered_favorites = self.apply_favorites_filters(
            favorites, selected_collection, selected_priority,
            selected_status, selected_position
        )

        if not filtered_favorites:
            st.warning("🚫 No favorites match the selected filters")
            return

        st.markdown(f"**Showing {len(filtered_favorites)} of {len(favorites)} favorite players**")

        # Sort options
        sort_by = st.selectbox(
            "Sort by:",
            ["Date Added (Newest)", "Date Added (Oldest)", "Player Name", "Priority", "Age"],
            key="favorites_sort"
        )

        # Sort favorites
        sorted_favorites = self.sort_favorites(filtered_favorites, sort_by)

        # Display favorites
        for fav_id, favorite in sorted_favorites.items():
            self.show_favorite_card(fav_id, favorite)

    def apply_favorites_filters(self, favorites: Dict, collection: str, priority: str,
                                status: str, position: str) -> Dict:
        """Apply filters to favorites"""
        filtered = {}

        for fav_id, favorite in favorites.items():
            # Collection filter
            if collection != "All" and favorite['collection'] != collection:
                continue

            # Priority filter
            if priority != "All" and favorite['priority'] != priority:
                continue

            # Status filter
            if status != "All" and favorite['status'] != status:
                continue

            # Position filter
            if position != "All" and favorite['position'] != position:
                continue

            filtered[fav_id] = favorite

        return filtered

    def sort_favorites(self, favorites: Dict, sort_by: str) -> Dict:
        """Sort favorites based on criteria"""
        try:
            if sort_by == "Date Added (Newest)":
                sorted_items = sorted(
                    favorites.items(),
                    key=lambda x: x[1]['added_date'],
                    reverse=True
                )
            elif sort_by == "Date Added (Oldest)":
                sorted_items = sorted(
                    favorites.items(),
                    key=lambda x: x[1]['added_date']
                )
            elif sort_by == "Player Name":
                sorted_items = sorted(
                    favorites.items(),
                    key=lambda x: x[1]['player_name']
                )
            elif sort_by == "Priority":
                priority_order = {"High": 3, "Medium": 2, "Low": 1}
                sorted_items = sorted(
                    favorites.items(),
                    key=lambda x: priority_order.get(x[1]['priority'], 0),
                    reverse=True
                )
            elif sort_by == "Age":
                sorted_items = sorted(
                    favorites.items(),
                    key=lambda x: x[1]['age'] if isinstance(x[1]['age'], (int, float)) else 0
                )
            else:
                sorted_items = list(favorites.items())

            return dict(sorted_items)

        except Exception as e:
            st.error(f"Error sorting favorites: {str(e)}")
            return favorites

    def show_favorite_card(self, fav_id: str, favorite: Dict):
        """Show individual favorite player card"""
        with st.container():
            # Header
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(favorite['priority'], "⚪")
                status_icon = {"Scouting": "🔍", "Contacted": "📞", "Negotiating": "💬", "Signed": "✅",
                               "Rejected": "❌"}.get(favorite['status'], "⚪")

                st.markdown(f"### {priority_icon} {favorite['player_name']} ({favorite['position']})")
                st.caption(
                    f"{status_icon} {favorite['status']} | {favorite['team']} | Age: {favorite['age']} | {favorite['nationality']}")

            with col2:
                if st.button("👁️ View Profile", key=f"view_profile_{fav_id}"):
                    st.session_state.selected_player = {
                        'name': favorite['player_name'],
                        'position': favorite['position']
                    }
                    st.session_state.show_player_profile = True
                    st.rerun()

            with col3:
                if st.button("⚙️ Manage", key=f"manage_{fav_id}"):
                    st.session_state[f"show_manage_{fav_id}"] = True
                    st.rerun()

            # Show management panel if requested
            if st.session_state.get(f"show_manage_{fav_id}", False):
                self.show_management_panel(fav_id, favorite)

            # Show basic info
            if favorite.get('reason'):
                st.markdown(f"**Reason:** {favorite['reason']}")

            if favorite.get('notes'):
                with st.expander("📝 Notes"):
                    for i, note in enumerate(favorite['notes']):
                        st.markdown(f"• {note}")

            st.markdown("---")

    def show_management_panel(self, fav_id: str, favorite: Dict):
        """Show management panel for a favorite"""
        with st.expander("⚙️ Manage Favorite", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                # Update status
                new_status = st.selectbox(
                    "Status:",
                    ["Scouting", "Contacted", "Negotiating", "Signed", "Rejected"],
                    index=["Scouting", "Contacted", "Negotiating", "Signed", "Rejected"].index(favorite['status']),
                    key=f"status_{fav_id}"
                )

                # Update priority
                new_priority = st.selectbox(
                    "Priority:",
                    ["High", "Medium", "Low"],
                    index=["High", "Medium", "Low"].index(favorite['priority']),
                    key=f"priority_{fav_id}"
                )

            with col2:
                # Update collection
                new_collection = st.text_input(
                    "Collection:",
                    value=favorite['collection'],
                    key=f"collection_{fav_id}"
                )

                # Update reason
                new_reason = st.text_area(
                    "Reason:",
                    value=favorite['reason'],
                    key=f"reason_{fav_id}"
                )

            # Add note
            new_note = st.text_input(
                "Add Note:",
                placeholder="Enter a new note...",
                key=f"new_note_{fav_id}"
            )

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Update", key=f"update_{fav_id}"):
                    updates = {
                        'status': new_status,
                        'priority': new_priority,
                        'collection': new_collection,
                        'reason': new_reason
                    }

                    if new_note.strip():
                        updates['notes'] = favorite.get('notes', []) + [
                            f"{datetime.now().strftime('%Y-%m-%d')}: {new_note}"]

                    if self.update_favorite(fav_id, updates):
                        st.success("Updated!")
                        st.session_state[f"show_manage_{fav_id}"] = False
                        st.rerun()

            with col2:
                if st.button("🗑️ Remove", key=f"remove_{fav_id}"):
                    if self.remove_from_favorites(fav_id):
                        st.success("Removed from favorites!")
                        st.rerun()

            with col3:
                if st.button("❌ Cancel", key=f"cancel_{fav_id}"):
                    st.session_state[f"show_manage_{fav_id}"] = False
                    st.rerun()

    def export_favorites_json(self) -> Optional[str]:
        """Export favorites as JSON"""
        try:
            favorites = self.load_favorites()
            if favorites:
                export_data = {
                    'export_type': 'favorites',
                    'version': '1.0',
                    'export_date': datetime.now().isoformat(),
                    'favorites': favorites
                }
                return json.dumps(export_data, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Error exporting favorites: {str(e)}")
        return None

    def import_favorites_json(self, json_data: str) -> bool:
        """Import favorites from JSON"""
        try:
            import_data = json.loads(json_data)

            if 'favorites' not in import_data:
                st.error("Invalid favorites file format")
                return False

            # Load existing favorites
            existing_favorites = self.load_favorites()

            # Merge imported favorites
            imported_count = 0
            for fav_id, favorite in import_data['favorites'].items():
                existing_favorites[fav_id] = favorite
                imported_count += 1

            # Save merged favorites
            if self.save_favorites(existing_favorites):
                st.success(f"Imported {imported_count} favorite players")
                return True
            else:
                st.error("Failed to save imported favorites")
                return False

        except Exception as e:
            st.error(f"Error importing favorites: {str(e)}")
            return False

    def get_collections(self) -> List[str]:
        """Get all collections"""
        favorites = self.load_favorites()
        collections = set()
        for favorite in favorites.values():
            collections.add(favorite.get('collection', 'General'))
        return sorted(list(collections))

    def get_favorites_by_status(self, status: str) -> Dict:
        """Get favorites by status"""
        favorites = self.load_favorites()
        return {fav_id: fav for fav_id, fav in favorites.items() if fav['status'] == status}

    def get_favorites_summary(self) -> Dict:
        """Get summary statistics for favorites"""
        favorites = self.load_favorites()

        if not favorites:
            return {}

        summary = {
            'total': len(favorites),
            'by_status': {},
            'by_priority': {},
            'by_position': {},
            'by_collection': {}
        }

        for favorite in favorites.values():
            # By status
            status = favorite['status']
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1

            # By priority
            priority = favorite['priority']
            summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1

            # By position
            position = favorite['position']
            summary['by_position'][position] = summary['by_position'].get(position, 0) + 1

            # By collection
            collection = favorite['collection']
            summary['by_collection'][collection] = summary['by_collection'].get(collection, 0) + 1

        return summary