1. Install a front-end (we recommend @qnc/qnc_data_tables)
2. `pip install qnc_data_tables`
3. Create a utility function to render a qnc_data_tables.TableManager as whatever markup is required by your front-end. If you're using @qnc/qnc_data_tables, then `test_project.render_table_manager.render_table_manager` is a working sample/starting point.
4. In a view for a page that renders a data table:
- create a qnc_data_tables.TableManager instance
- if request.method == POST, return table_manager.handle(...)
- otherwise, use your utility function to render the table_manager on your page