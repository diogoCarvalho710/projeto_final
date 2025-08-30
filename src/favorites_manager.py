import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime


class FavoritesManager:
    """Manages favorite players, configurations, and custom collections"""

    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.config_dir = Path("data/configs")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.favorites_file = self.config_dir / "favorites.json"
        self.collections_file = self.config_dir / "collections.json"

    def add_to_favorites(self, player_name: str, position: str, reason: str = "",
                         tags: List[str] = None, collection: str = "Default") -> bool:
        """Add a player to favorites with enhanced metadata"""

        if tags is None:
            tags = []

        # Get player data
        if position not in self.data_processor.dataframes:
            st.error(f"Position {position} not found")
            return False

        position_df = self.data_processor.dataframes[position]
        player_data = position_df[position_df['Jogador'] == player_name]

        if player_data.empty:
            st.error(f"Player {player_name} not found in {position}")
            return False

        # Extract detailed player info
        player_info = player_data.iloc[0]

        # Create comprehensive favorite entry
        favorite_entry = {
            'name': player_name,
            'position': position,
            'team': player_info.get('Time', 'Unknown'),
            'age': int(player_info.get('Idade', 0)),
            'nationality': player_info.get('Nacionalidade', 'Unknown'),
            'height': player_info.get('Altura', 'Unknown'),
            'foot': player_info.get('Pé', 'Unknown'),
            'minutes': int(player_info.get('Minutos jogados', 0)),
            'matches': int(player_info.get('Partidas jogadas', 0)),
            'goals': int(player_info.get('Gols', 0)),
            'assists': int(player_info.get('Assistências', 0)),
            'market_value': player_info.get('Valor de mercado', 'Unknown'),
            'contract_expires': player_info.get('Contrato expira em', 'Unknown'),
            'birth_date': player_info.get('Data de nascimento', 'Unknown'),
            'reason': reason,
            'tags': tags,
            'collection': collection,
            'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'notes': '',
            'rating': 0,  # User rating 1-5
            'priority': 'medium',  # low, medium, high, urgent
            'status': 'scouting'  # scouting, contacted, negotiating, signed, rejected
        }

        # Load existing favorites
        favorites = self.load_favorites()

        # Check if already in favorites
        favorite_id = f"{player_name}_{position}_{player_info.get('Time', 'Unknown')}"
        if favorite_id in favorites:
            st.warning(f"{player_name} is already in your favorites!")
            return False

        # Add to favorites
        favorites[favorite_id] = favorite_entry

        # Save favorites
        if self.save_favorites(favorites):
            st.success(f"Added {player_name} to favorites!")
            return True
        else:
            st.error("Failed to add to favorites")
            return False

    def remove_from_favorites(self, favorite_id: str) -> bool:
        """Remove a player from favorites"""

        favorites = self.load_favorites()

        if favorite_id in favorites:
            player_name = favorites[favorite_id]['name']
            del favorites[favorite_id]

            if self.save_favorites(favorites):
                st.success(f"Removed {player_name} from favorites")
                return True
            else:
                st.error("Failed to remove from favorites")
                return False
        else:
            st.warning("Player not found in favorites")
            return False

    def update_favorite(self, favorite_id: str, updates: Dict) -> bool:
        """Update favorite player information"""

        favorites = self.load_favorites()

        if favorite_id not in favorites:
            return False

        # Update fields
        for key, value in updates.items():
            favorites[favorite_id][key] = value

        favorites[favorite_id]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return self.save_favorites(favorites)

    def load_favorites(self) -> Dict:
        """Load favorites from JSON file"""

        if not self.favorites_file.exists():
            return {}

        try:
            with open(self.favorites_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading favorites: {str(e)}")
            return {}

    def save_favorites(self, favorites: Dict) -> bool:
        """Save favorites to JSON file"""

        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving favorites: {str(e)}")
            return False

    def get_favorites_count(self) -> int:
        """Get total number of favorite players"""
        return len(self.load_favorites())

    def get_favorites_by_position(self, position: str) -> List[Dict]:
        """Get favorite players for a specific position"""

        favorites = self.load_favorites()
        position_favorites = []

        for favorite_id, favorite_data in favorites.items():
            if favorite_data.get('position') == position:
                favorite_data['id'] = favorite_id
                position_favorites.append(favorite_data)

        # Sort by priority then by added date
        priority_order = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
        position_favorites.sort(
            key=lambda x: (priority_order.get(x.get('priority', 'medium'), 2),
                           x.get('added_date', '')),
            reverse=True
        )

        return position_favorites

    def get_favorites_by_collection(self, collection: str) -> List[Dict]:
        """Get favorites by collection"""

        favorites = self.load_favorites()
        collection_favorites = []

        for favorite_id, favorite_data in favorites.items():
            if favorite_data.get('collection', 'Default') == collection:
                favorite_data['id'] = favorite_id
                collection_favorites.append(favorite_data)

        return collection_favorites

    def get_favorites_by_tag(self, tag: str) -> List[Dict]:
        """Get favorite players with a specific tag"""

        favorites = self.load_favorites()
        tagged_favorites = []

        for favorite_id, favorite_data in favorites.items():
            if tag in favorite_data.get('tags', []):
                favorite_data['id'] = favorite_id
                tagged_favorites.append(favorite_data)

        return tagged_favorites

    def get_all_tags(self) -> List[str]:
        """Get all tags used in favorites"""

        favorites = self.load_favorites()
        all_tags = set()

        for favorite_data in favorites.values():
            all_tags.update(favorite_data.get('tags', []))

        return sorted(list(all_tags))

    def get_all_collections(self) -> List[str]:
        """Get all collections"""

        favorites = self.load_favorites()
        collections = set()

        for favorite_data in favorites.values():
            collections.add(favorite_data.get('collection', 'Default'))

        return sorted(list(collections))

    def is_favorite(self, player_name: str, position: str, team: str = None) -> bool:
        """Check if a player is in favorites"""

        favorites = self.load_favorites()

        for favorite_data in favorites.values():
            if (favorite_data['name'] == player_name and
                    favorite_data['position'] == position):
                if team is None or favorite_data.get('team') == team:
                    return True

        return False

    def show_favorites_ui(self):
        """Show comprehensive favorites management UI"""

        st.subheader("Favorite Players Management")

        favorites = self.load_favorites()

        if not favorites:
            st.info("No favorite players yet. Add players to favorites from the scouting page!")
            self._show_favorites_help()
            return

        # Summary dashboard
        self._show_favorites_dashboard(favorites)

        st.markdown("---")

        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Browse Favorites", "Collections", "Analytics", "Bulk Actions"])

        with tab1:
            self._show_browse_favorites(favorites)

        with tab2:
            self._show_collections_management()

        with tab3:
            self._show_favorites_analytics(favorites)

        with tab4:
            self._show_bulk_actions(favorites)

    def _show_favorites_dashboard(self, favorites: Dict):
        """Show favorites summary dashboard"""

        # Calculate statistics
        total_count = len(favorites)
        positions = set(f.get('position', 'Unknown') for f in favorites.values())
        teams = set(f.get('team', 'Unknown') for f in favorites.values())
        collections = set(f.get('collection', 'Default') for f in favorites.values())
        tags = self.get_all_tags()

        # Priority distribution
        priority_counts = {}
        for fav in favorites.values():
            priority = fav.get('priority', 'medium')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Status distribution
        status_counts = {}
        for fav in favorites.values():
            status = fav.get('status', 'scouting')
            status_counts[status] = status_counts.get(status, 0) + 1

        # Display dashboard
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Favorites", total_count)
        with col2:
            st.metric("Positions", len(positions))
        with col3:
            st.metric("Teams", len(teams))
        with col4:
            st.metric("Collections", len(collections))
        with col5:
            st.metric("Tags", len(tags))

        # Priority and status overview
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Priority Distribution:**")
            for priority in ['urgent', 'high', 'medium', 'low']:
                count = priority_counts.get(priority, 0)
                if count > 0:
                    icon = {"urgent": "🚨", "high": "🔥", "medium": "⚡", "low": "📝"}[priority]
                    st.markdown(f"{icon} {priority.title()}: {count}")

        with col2:
            st.markdown("**Status Distribution:**")
            for status in ['scouting', 'contacted', 'negotiating', 'signed', 'rejected']:
                count = status_counts.get(status, 0)
                if count > 0:
                    icon = {"scouting": "🔍", "contacted": "📞", "negotiating": "💬",
                            "signed": "✅", "rejected": "❌"}[status]
                    st.markdown(f"{icon} {status.title()}: {count}")

    def _show_browse_favorites(self, favorites: Dict):
        """Show browsing interface for favorites"""

        # Filters
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            positions = ['All'] + sorted(set(f.get('position', 'Unknown') for f in favorites.values()))
            position_filter = st.selectbox("Position", positions, key="fav_position_filter")

        with col2:
            collections = ['All'] + self.get_all_collections()
            collection_filter = st.selectbox("Collection", collections, key="fav_collection_filter")

        with col3:
            priorities = ['All', 'urgent', 'high', 'medium', 'low']
            priority_filter = st.selectbox("Priority", priorities, key="fav_priority_filter")

        with col4:
            statuses = ['All', 'scouting', 'contacted', 'negotiating', 'signed', 'rejected']
            status_filter = st.selectbox("Status", statuses, key="fav_status_filter")

        # Additional filters
        col1, col2 = st.columns(2)
        with col1:
            tags = ['All'] + self.get_all_tags()
            tag_filter = st.selectbox("Tag", tags, key="fav_tag_filter")

        with col2:
            sort_options = ['Added Date (Newest)', 'Added Date (Oldest)', 'Name A-Z', 'Name Z-A',
                            'Age (Youngest)', 'Age (Oldest)', 'Priority', 'Rating']
            sort_by = st.selectbox("Sort by", sort_options, key="fav_sort_by")

        # Apply filters
        filtered_favorites = self._apply_favorite_filters(
            favorites, position_filter, collection_filter, priority_filter,
            status_filter, tag_filter, sort_by
        )

        if not filtered_favorites:
            st.info("No favorites match the current filters")
            return

        st.markdown(f"**Showing {len(filtered_favorites)} favorites:**")

        # Display favorites
        for favorite_id, favorite_data in filtered_favorites.items():
            self._show_favorite_card(favorite_id, favorite_data)

    def _apply_favorite_filters(self, favorites: Dict, position_filter: str, collection_filter: str,
                                priority_filter: str, status_filter: str, tag_filter: str, sort_by: str) -> Dict:
        """Apply filters to favorites"""

        filtered = favorites.copy()

        # Apply filters
        if position_filter != 'All':
            filtered = {k: v for k, v in filtered.items() if v.get('position') == position_filter}

        if collection_filter != 'All':
            filtered = {k: v for k, v in filtered.items() if v.get('collection', 'Default') == collection_filter}

        if priority_filter != 'All':
            filtered = {k: v for k, v in filtered.items() if v.get('priority', 'medium') == priority_filter}

        if status_filter != 'All':
            filtered = {k: v for k, v in filtered.items() if v.get('status', 'scouting') == status_filter}

        if tag_filter != 'All':
            filtered = {k: v for k, v in filtered.items() if tag_filter in v.get('tags', [])}

        # Apply sorting
        if sort_by == 'Added Date (Newest)':
            filtered = dict(sorted(filtered.items(), key=lambda x: x[1].get('added_date', ''), reverse=True))
        elif sort_by == 'Added Date (Oldest)':
            filtered = dict(sorted(filtered.items(), key=lambda x: x[1].get('added_date', '')))
        elif sort_by == 'Name A-Z':
            filtered = dict(sorted(filtered.items(), key=lambda x: x[1].get('name', '')))
        elif sort_by == 'Name Z-A':
            filtered = dict(sorted(filtered.items(), key=lambda x: x[1].get('name', ''), reverse=True))
        elif sort_by == 'Age (Youngest)':
            filtered = dict(sorted(filtered.items(), key=lambda x: x[1].get('age', 99)))
        elif sort_by == 'Age (Oldest)':
            filtered = dict(sorted(filtered.items(), key=lambda x: x[1].get('age', 0), reverse=True))
        elif sort_by == 'Priority':
            priority_order = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
            filtered = dict(sorted(filtered.items(),
                                   key=lambda x: priority_order.get(x[1].get('priority', 'medium'), 2),
                                   reverse=True))
        elif sort_by == 'Rating':
            filtered = dict(sorted(filtered.items(), key=lambda x: x[1].get('rating', 0), reverse=True))

        return filtered

    def _show_favorite_card(self, favorite_id: str, favorite_data: Dict):
        """Show individual favorite player card with management options"""

        with st.container():
            # Card header
            col1, col2 = st.columns([4, 1])

            with col1:
                # Priority and status indicators
                priority_icons = {'urgent': '🚨', 'high': '🔥', 'medium': '⚡', 'low': '📝'}
                status_icons = {'scouting': '🔍', 'contacted': '📞', 'negotiating': '💬',
                                'signed': '✅', 'rejected': '❌'}

                priority_icon = priority_icons.get(favorite_data.get('priority', 'medium'), '⚡')
                status_icon = status_icons.get(favorite_data.get('status', 'scouting'), '🔍')

                st.markdown(f"**{priority_icon} {status_icon} {favorite_data['name']}**")
                st.caption(f"{favorite_data['position']} | {favorite_data['team']} | Age: {favorite_data['age']}")

            with col2:
                # Rating display
                rating = favorite_data.get('rating', 0)
                if rating > 0:
                    stars = '⭐' * rating
                    st.markdown(f"**{stars}**")

            # Player details
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Minutes", f"{favorite_data['minutes']:,}")
            with col2:
                st.metric("Goals", favorite_data.get('goals', 0))
            with col3:
                st.metric("Assists", favorite_data.get('assists', 0))
            with col4:
                st.metric("Matches", favorite_data.get('matches', 0))

            # Additional info
            if favorite_data.get('reason'):
                st.caption(f"📝 Reason: {favorite_data['reason']}")

            if favorite_data.get('notes'):
                st.caption(f"📄 Notes: {favorite_data['notes']}")

            # Tags
            if favorite_data.get('tags'):
                tags_html = " ".join([
                    f"<span style='background-color: #4CAF50; color: white; padding: 2px 6px; border-radius: 12px; font-size: 0.8em;'>#{tag}</span>"
                    for tag in favorite_data['tags']
                ])
                st.markdown(tags_html, unsafe_allow_html=True)

            # Action buttons
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                if st.button("👁️ View", key=f"view_{favorite_id}", help="View player profile"):
                    st.session_state.selected_player = {
                        'name': favorite_data['name'],
                        'position': favorite_data['position']
                    }
                    st.session_state.current_page = 'player_profile'
                    st.rerun()

            with col2:
                if st.button("✏️ Edit", key=f"edit_{favorite_id}", help="Edit favorite"):
                    self._show_edit_favorite_modal(favorite_id, favorite_data)

            with col3:
                if st.button("📋 Notes", key=f"notes_{favorite_id}", help="Add/edit notes"):
                    self._show_notes_modal(favorite_id, favorite_data)

            with col4:
                if st.button("🏷️ Tags", key=f"tags_{favorite_id}", help="Manage tags"):
                    self._show_tags_modal(favorite_id, favorite_data)

            with col5:
                if st.button("🗑️ Remove", key=f"remove_{favorite_id}", help="Remove from favorites"):
                    if st.session_state.get(f"confirm_remove_{favorite_id}"):
                        self.remove_from_favorites(favorite_id)
                        st.rerun()
                    else:
                        st.session_state[f"confirm_remove_{favorite_id}"] = True
                        st.warning("Click again to confirm removal")

            st.markdown("---")

    def _show_edit_favorite_modal(self, favorite_id: str, favorite_data: Dict):
        """Show modal for editing favorite player"""

        with st.expander(f"Edit {favorite_data['name']}", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                new_priority = st.selectbox(
                    "Priority",
                    ['low', 'medium', 'high', 'urgent'],
                    index=['low', 'medium', 'high', 'urgent'].index(favorite_data.get('priority', 'medium')),
                    key=f"edit_priority_{favorite_id}"
                )

                new_status = st.selectbox(
                    "Status",
                    ['scouting', 'contacted', 'negotiating', 'signed', 'rejected'],
                    index=['scouting', 'contacted', 'negotiating', 'signed', 'rejected'].index(
                        favorite_data.get('status', 'scouting')),
                    key=f"edit_status_{favorite_id}"
                )

            with col2:
                new_rating = st.slider(
                    "Rating (1-5 stars)",
                    1, 5,
                    value=favorite_data.get('rating', 3),
                    key=f"edit_rating_{favorite_id}"
                )

                new_collection = st.text_input(
                    "Collection",
                    value=favorite_data.get('collection', 'Default'),
                    key=f"edit_collection_{favorite_id}"
                )

            new_reason = st.text_area(
                "Reason/Interest",
                value=favorite_data.get('reason', ''),
                key=f"edit_reason_{favorite_id}"
            )

            if st.button("Save Changes", key=f"save_edit_{favorite_id}"):
                updates = {
                    'priority': new_priority,
                    'status': new_status,
                    'rating': new_rating,
                    'collection': new_collection,
                    'reason': new_reason
                }

                if self.update_favorite(favorite_id, updates):
                    st.success("Favorite updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update favorite")

    def _show_notes_modal(self, favorite_id: str, favorite_data: Dict):
        """Show modal for managing notes"""

        with st.expander(f"Notes for {favorite_data['name']}", expanded=True):
            current_notes = favorite_data.get('notes', '')

            new_notes = st.text_area(
                "Notes",
                value=current_notes,
                height=100,
                help="Add scouting notes, observations, or any relevant information",
                key=f"notes_text_{favorite_id}"
            )

            if st.button("Save Notes", key=f"save_notes_{favorite_id}"):
                if self.update_favorite(favorite_id, {'notes': new_notes}):
                    st.success("Notes saved successfully!")
                    st.rerun()

    def _show_tags_modal(self, favorite_id: str, favorite_data: Dict):
        """Show modal for managing tags"""

        with st.expander(f"Tags for {favorite_data['name']}", expanded=True):
            current_tags = favorite_data.get('tags', [])
            all_existing_tags = self.get_all_tags()

            # Select from existing tags
            selected_existing = st.multiselect(
                "Existing tags",
                all_existing_tags,
                default=[tag for tag in current_tags if tag in all_existing_tags],
                key=f"existing_tags_{favorite_id}"
            )

            # Add new tags
            new_tags_input = st.text_input(
                "New tags (comma-separated)",
                help="Enter new tags separated by commas",
                key=f"new_tags_{favorite_id}"
            )

            new_tags = [tag.strip() for tag in new_tags_input.split(',') if tag.strip()] if new_tags_input else []

            # Combine all tags
            all_tags = list(set(selected_existing + new_tags))

            if st.button("Save Tags", key=f"save_tags_{favorite_id}"):
                if self.update_favorite(favorite_id, {'tags': all_tags}):
                    st.success("Tags updated successfully!")
                    st.rerun()

    def _show_collections_management(self):
        """Show collections management interface"""

        st.subheader("Collections Management")

        collections = self.get_all_collections()

        if not collections:
            st.info("No collections yet. Players are automatically added to 'Default' collection.")
            return

        # Collection statistics
        collection_stats = {}
        favorites = self.load_favorites()

        for fav in favorites.values():
            collection = fav.get('collection', 'Default')
            if collection not in collection_stats:
                collection_stats[collection] = {'count': 0, 'positions': set(), 'teams': set()}

            collection_stats[collection]['count'] += 1
            collection_stats[collection]['positions'].add(fav.get('position', 'Unknown'))
            collection_stats[collection]['teams'].add(fav.get('team', 'Unknown'))

        # Display collections
        for collection in collections:
            stats = collection_stats.get(collection, {'count': 0, 'positions': set(), 'teams': set()})

            with st.expander(f"📁 {collection} ({stats['count']} players)", expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Players", stats['count'])
                with col2:
                    st.metric("Positions", len(stats['positions']))
                with col3:
                    st.metric("Teams", len(stats['teams']))

                # Show players in this collection
                collection_favorites = self.get_favorites_by_collection(collection)

                if collection_favorites:
                    players_text = ", ".join(
                        [f"{fav['name']} ({fav['position']})" for fav in collection_favorites[:10]])
                    if len(collection_favorites) > 10:
                        players_text += f" and {len(collection_favorites) - 10} more..."
                    st.caption(f"Players: {players_text}")

    def _show_favorites_analytics(self, favorites: Dict):
        """Show analytics about favorites"""

        st.subheader("Favorites Analytics")

        if not favorites:
            st.info("No favorites data for analytics")
            return

        # Age distribution
        ages = [fav.get('age', 0) for fav in favorites.values()]
        age_ranges = {'Under 20': 0, '20-25': 0, '26-30': 0, '31-35': 0, 'Over 35': 0}

        for age in ages:
            if age < 20:
                age_ranges['Under 20'] += 1
            elif age <= 25:
                age_ranges['20-25'] += 1
            elif age <= 30:
                age_ranges['26-30'] += 1
            elif age <= 35:
                age_ranges['31-35'] += 1
            else:
                age_ranges['Over 35'] += 1

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Age Distribution:**")
            for age_range, count in age_ranges.items():
                if count > 0:
                    st.markdown(f"• {age_range}: {count}")

        # Position distribution
        with col2:
            positions = {}
            for fav in favorites.values():
                pos = fav.get('position', 'Unknown')
                positions[pos] = positions.get(pos, 0) + 1

            st.markdown("**Position Distribution:**")
            for pos, count in sorted(positions.items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"• {pos}: {count}")

        # Team distribution
        st.markdown("**Team Distribution:**")
        teams = {}
        for fav in favorites.values():
            team = fav.get('team', 'Unknown')
            teams[team] = teams.get(team, 0) + 1

        top_teams = sorted(teams.items(), key=lambda x: x[1], reverse=True)[:10]
        for team, count in top_teams:
            st.markdown(f"• {team}: {count}")

        # Recent additions
        st.markdown("**Recent Additions (Last 7 days):**")
        recent_favorites = []
        cutoff_date = datetime.now().strftime('%Y-%m-%d')

        for fav in favorites.values():
            added_date = fav.get('added_date', '')
            if added_date >= cutoff_date:
                recent_favorites.append(fav)

        if recent_favorites:
            for fav in recent_favorites[-5:]:  # Last 5
                st.markdown(f"• {fav['name']} ({fav['position']}) - {fav['team']}")
        else:
            st.caption("No recent additions")

    def _show_bulk_actions(self, favorites: Dict):
        """Show bulk action interface"""

        st.subheader("Bulk Actions")

        if not favorites:
            st.info("No favorites for bulk actions")
            return

        # Export/Import section
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Export Favorites:**")

            export_format = st.radio(
                "Export format:",
                ["JSON (Full data)", "CSV (Summary)"],
                key="export_format"
            )

            if st.button("📥 Export Favorites"):
                if export_format == "JSON (Full data)":
                    export_data = self.export_favorites_json()
                    if export_data:
                        st.download_button(
                            "Download JSON",
                            export_data,
                            "favorites.json",
                            "application/json"
                        )
                else:
                    export_data = self.export_favorites_csv()
                    if export_data:
                        st.download_button(
                            "Download CSV",
                            export_data,
                            "favorites.csv",
                            "text/csv"
                        )

        with col2:
            st.markdown("**Import Favorites:**")

            uploaded_file = st.file_uploader(
                "Upload favorites file",
                type=['json'],
                help="Upload a JSON file with favorites data",
                key="import_favorites"
            )

            if uploaded_file and st.button("📤 Import Favorites"):
                try:
                    import_data = uploaded_file.getvalue().decode('utf-8')
                    if self.import_favorites_json(import_data):
                        st.success("Favorites imported successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

        # Bulk update section
        st.markdown("---")
        st.markdown("**Bulk Update:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            bulk_priority = st.selectbox(
                "Set Priority for All",
                ['', 'low', 'medium', 'high', 'urgent'],
                key="bulk_priority"
            )

            if bulk_priority and st.button("Update All Priorities"):
                count = self._bulk_update_field('priority', bulk_priority)
                st.success(f"Updated priority for {count} favorites")

        with col2:
            bulk_status = st.selectbox(
                "Set Status for All",
                ['', 'scouting', 'contacted', 'negotiating', 'signed', 'rejected'],
                key="bulk_status"
            )

            if bulk_status and st.button("Update All Statuses"):
                count = self._bulk_update_field('status', bulk_status)
                st.success(f"Updated status for {count} favorites")

        with col3:
            bulk_collection = st.text_input(
                "Move All to Collection",
                key="bulk_collection"
            )

            if bulk_collection and st.button("Move All to Collection"):
                count = self._bulk_update_field('collection', bulk_collection)
                st.success(f"Moved {count} favorites to collection '{bulk_collection}'")

        # Cleanup section
        st.markdown("---")
        st.markdown("**Cleanup Actions:**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🧹 Remove Rejected Players"):
                count = self._bulk_remove_by_status('rejected')
                if count > 0:
                    st.success(f"Removed {count} rejected players")
                    st.rerun()
                else:
                    st.info("No rejected players to remove")

        with col2:
            if st.button("🗑️ Clear All Favorites", type="primary"):
                if st.session_state.get('confirm_clear_all'):
                    self.clear_all_favorites()
                    st.success("All favorites cleared!")
                    st.rerun()
                else:
                    st.session_state['confirm_clear_all'] = True
                    st.warning("Click again to confirm clearing ALL favorites")

    def _bulk_update_field(self, field: str, value: str) -> int:
        """Bulk update a field for all favorites"""

        favorites = self.load_favorites()
        count = 0

        for favorite_id in favorites:
            favorites[favorite_id][field] = value
            favorites[favorite_id]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            count += 1

        if self.save_favorites(favorites):
            return count
        return 0

    def _bulk_remove_by_status(self, status: str) -> int:
        """Remove all favorites with specified status"""

        favorites = self.load_favorites()
        to_remove = []

        for favorite_id, favorite_data in favorites.items():
            if favorite_data.get('status') == status:
                to_remove.append(favorite_id)

        for favorite_id in to_remove:
            del favorites[favorite_id]

        if self.save_favorites(favorites):
            return len(to_remove)
        return 0

    def clear_all_favorites(self) -> bool:
        """Clear all favorites"""
        return self.save_favorites({})

    def _show_favorites_help(self):
        """Show help information about favorites system"""

        with st.expander("💡 How to Use Favorites System"):
            st.markdown("""
            **Getting Started:**
            1. Add players from the Scouting page using the ➕ buttons
            2. Organize players with collections, tags, and priorities
            3. Track scouting progress with status updates
            4. Add notes and ratings for detailed analysis

            **Features:**
            - **Collections**: Group players by criteria (e.g., "Summer Targets", "Youth Prospects")
            - **Tags**: Add flexible labels (#pace, #leadership, #bargain)
            - **Priority**: Mark urgency (🚨 Urgent, 🔥 High, ⚡ Medium, 📝 Low)
            - **Status**: Track progress (🔍 Scouting → 📞 Contacted → 💬 Negotiating → ✅ Signed)
            - **Ratings**: Rate players 1-5 stars based on your assessment
            - **Notes**: Add detailed scouting observations

            **Bulk Actions:**
            - Export/import favorites for backup
            - Bulk update priorities, statuses, or collections
            - Clean up rejected players

            **Analytics:**
            - View distribution by age, position, team
            - Track recent additions and trends
            """)

    def export_favorites_json(self) -> Optional[str]:
        """Export favorites as JSON"""

        favorites = self.load_favorites()
        if not favorites:
            return None

        try:
            export_data = {
                'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version': '1.0',
                'favorites_count': len(favorites),
                'favorites': favorites
            }
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Error exporting favorites: {str(e)}")
            return None

    def export_favorites_csv(self) -> Optional[str]:
        """Export favorites as CSV"""

        favorites = self.load_favorites()
        if not favorites:
            return None

        try:
            # Create DataFrame
            data = []
            for favorite_id, fav in favorites.items():
                data.append({
                    'Name': fav['name'],
                    'Position': fav['position'],
                    'Team': fav['team'],
                    'Age': fav['age'],
                    'Nationality': fav['nationality'],
                    'Minutes': fav['minutes'],
                    'Goals': fav.get('goals', 0),
                    'Assists': fav.get('assists', 0),
                    'Priority': fav.get('priority', 'medium'),
                    'Status': fav.get('status', 'scouting'),
                    'Collection': fav.get('collection', 'Default'),
                    'Rating': fav.get('rating', 0),
                    'Tags': ', '.join(fav.get('tags', [])),
                    'Reason': fav.get('reason', ''),
                    'Notes': fav.get('notes', ''),
                    'Added Date': fav.get('added_date', ''),
                    'Market Value': fav.get('market_value', 'Unknown')
                })

            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        except Exception as e:
            st.error(f"Error exporting CSV: {str(e)}")
            return None

    def import_favorites_json(self, import_data: str) -> bool:
        """Import favorites from JSON"""

        try:
            data = json.loads(import_data)

            if 'favorites' not in data:
                st.error("Invalid import format - missing favorites data")
                return False

            imported_favorites = data['favorites']
            existing_favorites = self.load_favorites()

            # Count new vs existing
            new_count = 0
            updated_count = 0

            for favorite_id, favorite_data in imported_favorites.items():
                if favorite_id in existing_favorites:
                    updated_count += 1
                else:
                    new_count += 1

                existing_favorites[favorite_id] = favorite_data

            # Save updated favorites
            if self.save_favorites(existing_favorites):
                st.success(f"Import successful: {new_count} new favorites, {updated_count} updated")
                return True
            else:
                st.error("Failed to save imported favorites")
                return False

        except json.JSONDecodeError:
            st.error("Invalid JSON format")
            return False
        except Exception as e:
            st.error(f"Error importing favorites: {str(e)}")
            return False

    def get_favorite_suggestions(self, position: str, limit: int = 5) -> List[Dict]:
        """Get player suggestions based on existing favorites"""

        favorites = self.load_favorites()
        if not favorites:
            return []

        # Get favorite players' characteristics
        favorite_teams = set()
        favorite_nationalities = set()
        age_ranges = []

        for fav in favorites.values():
            if fav.get('position') == position:
                favorite_teams.add(fav.get('team', ''))
                favorite_nationalities.add(fav.get('nationality', ''))
                age_ranges.append(fav.get('age', 25))

        if not age_ranges:
            return []

        avg_age = sum(age_ranges) / len(age_ranges)
        age_tolerance = 3

        # Find similar players not in favorites
        if position not in self.data_processor.dataframes:
            return []

        position_df = self.data_processor.dataframes[position]
        suggestions = []

        for _, player in position_df.iterrows():
            player_name = player.get('Jogador', '')
            player_team = player.get('Time', '')
            player_age = player.get('Idade', 99)
            player_nationality = player.get('Nacionalidade', '')

            # Skip if already in favorites
            if self.is_favorite(player_name, position, player_team):
                continue

            # Calculate similarity score
            score = 0

            # Age similarity
            if abs(player_age - avg_age) <= age_tolerance:
                score += 30

            # Team similarity (but not same team)
            if player_team in favorite_teams and player_team != '':
                score += 20

            # Nationality similarity
            if player_nationality in favorite_nationalities and player_nationality != '':
                score += 25

            # Playing time (prefer regular players)
            minutes = player.get('Minutos jogados', 0)
            if minutes > 1000:
                score += 15
            elif minutes > 500:
                score += 10

            # Performance metrics (basic)
            if position in ['PL', 'EE', 'ED']:  # Attacking players
                goals = player.get('Gols', 0)
                assists = player.get('Assistências', 0)
                if goals + assists > 5:
                    score += 10
            elif position in ['DCE', 'DCD', 'MCD']:  # Defensive players
                tackles = player.get('Desarmes', 0)
                interceptions = player.get('Interceptações', 0)
                if tackles + interceptions > 50:
                    score += 10

            if score > 30:  # Minimum threshold
                suggestions.append({
                    'name': player_name,
                    'team': player_team,
                    'age': int(player_age),
                    'nationality': player_nationality,
                    'minutes': int(minutes),
                    'similarity_score': score,
                    'position': position
                })

        # Sort by similarity score and return top suggestions
        suggestions.sort(key=lambda x: x['similarity_score'], reverse=True)
        return suggestions[:limit]

    def show_suggestions_ui(self):
        """Show player suggestions based on favorites"""

        st.subheader("🎯 Player Suggestions")
        st.caption("Based on your favorite players' characteristics")

        favorites = self.load_favorites()
        if not favorites:
            st.info("Add some favorite players first to get personalized suggestions!")
            return

        # Get positions with favorites
        positions_with_favs = set(fav.get('position') for fav in favorites.values())

        for position in positions_with_favs:
            suggestions = self.get_favorite_suggestions(position)

            if suggestions:
                st.markdown(f"**{position} Suggestions:**")

                for i, suggestion in enumerate(suggestions):
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"**{i + 1}. {suggestion['name']}**")
                        st.caption(f"{suggestion['team']} | Age: {suggestion['age']} | {suggestion['nationality']}")
                        st.caption(
                            f"Minutes: {suggestion['minutes']:,} | Similarity: {suggestion['similarity_score']}%")

                    with col2:
                        if st.button("👁️ View", key=f"view_sugg_{position}_{i}", help="View player profile"):
                            st.session_state.selected_player = {
                                'name': suggestion['name'],
                                'position': position
                            }
                            st.session_state.current_page = 'player_profile'
                            st.rerun()

                    with col3:
                        if st.button("⭐ Add", key=f"add_sugg_{position}_{i}", help="Add to favorites"):
                            if self.add_to_favorites(
                                    suggestion['name'],
                                    position,
                                    reason="Suggested based on favorites",
                                    tags=["suggestion"],
                                    collection="Suggestions"
                            ):
                                st.rerun()

                st.markdown("---")