import requests

from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # session 需要這個金鑰

API_BASE_URL = "http://127.0.0.1:8000/api/v1"


# ==========================================
# 1. 登入
# ==========================================

# 警衛機制：每次請求前檢查是否已登入
@app.before_request
def check_login():
    # 定義不需要登入就可以訪問的頁面 (白名單)
    allowed_routes = ['login', 'static']
    
    # 如果使用者還沒登入 ('user' 不在 session 中)
    # 且 請求的頁面不在白名單內
    if 'user' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    try:
        response = requests.get(f"{API_BASE_URL}/dashboard/", timeout=5)
        data = response.json() if response.status_code == 200 else {}
    except:
        data = {}
        flash('無法連接儀表板數據 API', 'danger')

    # Ensure structure exists even if API fails
    kpi = data.get('kpi', {'total_sku': 0, 'monthly_inbound': 0, 'monthly_req': 0})
    low_stock = data.get('low_stock', [])
    activities = data.get('activities', [])

    return render_template('dashboard.html', kpi=kpi, low_stock=low_stock, activities=activities)

@app.route('/')
def index():
    # 首頁導向儀表板 (User requested Dashboard as Landing Page link, but Nav 'Dashboard' links here)
    # Reorganize: Dashboard -> Link to Home. So '/' should redirect to '/dashboard' if logged in.
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            # Call Backend Auth API
            resp = requests.post(f"{API_BASE_URL}/auth/login", json={"username": username, "password": password}, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    # Login Success
                    session['user'] = data['username']
                    session['staff_id'] = data['staff_id']
                    session['is_manager'] = data['is_manager']
                    return redirect(url_for('dashboard'))
                else:
                    flash(data.get("message", "Login failed"), 'danger')
            else:
                 flash(f"API Error: {resp.status_code}", 'danger')

        except Exception as e:
            flash(f"Connection Error: {e}", 'danger')

        return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)  # 清除 session
    flash('您已成功登出', 'info')
    return redirect(url_for('login'))

# ==========================================
# 1. 商品管理 (Products)
# ==========================================
@app.route('/product')
def product_page():
    try:
        response = requests.get(f"{API_BASE_URL}/products/", timeout=5)
        products = response.json() if response.status_code == 200 else []
    except:
        products = []
        flash('連線後端伺服器失敗，請確認 8000 port 是否開啟', 'danger')
    return render_template('product.html', products=products)

@app.route('/product/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        payload = {
            "prName": request.form['prName'],
            "prCategory": request.form['prCategory'],
            "prSpec": request.form['prSpec'] if request.form['prSpec'] else None
        }
        try:
            requests.post(f"{API_BASE_URL}/products/", json=payload, timeout=5)
            return redirect(url_for('product_page'))
        except Exception as e:
            flash(f'錯誤：{str(e)}', 'danger')
    return render_template('add_product.html')

@app.route('/product/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        requests.delete(f"{API_BASE_URL}/products/{product_id}", timeout=5)
    except:
        flash('刪除失敗', 'danger')
    return redirect(url_for('product_page'))


# ==========================================
# 2. 供應商管理 (Suppliers)
# ==========================================
@app.route('/supplier')
def supplier_page():
    try:
        response = requests.get(f"{API_BASE_URL}/suppliers/", timeout=5)
        suppliers = response.json() if response.status_code == 200 else []
    except:
        suppliers = []
    return render_template('supplier.html', suppliers=suppliers)

@app.route('/supplier/add', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        payload = {
            "suName": request.form['suName'],
            "suPhone": request.form['suPhone'],
            "suAddress": request.form['suAddress']
        }
        try:
            requests.post(f"{API_BASE_URL}/suppliers/", json=payload, timeout=5)
            return redirect(url_for('supplier_page'))
        except:
            flash('新增失敗', 'danger')
    return render_template('add_supplier.html')

@app.route('/supplier/delete/<int:supplier_id>', methods=['POST'])
def delete_supplier(supplier_id):
    try:
        requests.delete(f"{API_BASE_URL}/suppliers/{supplier_id}", timeout=5)
    except:
        pass
    return redirect(url_for('supplier_page'))


# ==========================================
# 3. 倉庫管理 (Warehouse)
# ==========================================
@app.route('/warehouse')
def warehouse_page():
    try:
        response = requests.get(f"{API_BASE_URL}/warehouse/", timeout=5)
        warehouses = response.json() if response.status_code == 200 else []
    except:
        warehouses = []
    return render_template('warehouse.html', warehouses=warehouses)

@app.route('/warehouse/add', methods=['GET', 'POST'])
def add_warehouse():
    if request.method == 'POST':
        payload = {
            "waName": request.form['waName'],
            "waLocation": request.form['waLocation']
        }
        requests.post(f"{API_BASE_URL}/warehouse/", json=payload)
        return redirect(url_for('warehouse_page'))
    return render_template('add_warehouse.html')

@app.route('/warehouse/delete/<int:warehouse_id>', methods=['POST'])
def delete_warehouse(warehouse_id):
    try:
        requests.delete(f"{API_BASE_URL}/warehouse/{warehouse_id}")
    except:
        pass
    return redirect(url_for('warehouse_page'))


# ==========================================
# 4. 員工管理 (Staff)
# ==========================================
@app.route('/staff')
def staff_page():
    if not session.get('is_manager'):
         flash('權限不足 (需要管理員權限)', 'danger')
         return redirect(url_for('dashboard'))

    try:
        response = requests.get(f"{API_BASE_URL}/staff/", timeout=5)
        staff_list = response.json() if response.status_code == 200 else []
        
        # 非Admin用戶無法看到Admin帳號
        if session.get('user') != 'Admin':
            staff_list = [s for s in staff_list if s.get('username') != 'Admin']
            
    except:
        staff_list = []
        flash('無法連接 API', 'danger')

    return render_template('staff.html', staff_list=staff_list)

@app.route('/staff/add', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        # Only Admin can grant manager rights
        is_manager = False
        if session.get('user') == 'Admin':
            is_manager = request.form.get('is_manager') == '1'
        
        payload = {
            "stName": request.form['stName'],
            "stDept": request.form['stDept'],
            "stTitle": request.form.get('stTitle', ''),
            "stPhone": request.form.get('stPhone', ''),
            "stEmail": request.form.get('stEmail', ''),
            "username": request.form['username'],
            "password": request.form['password'],
            "is_manager": is_manager
        }
        requests.post(f"{API_BASE_URL}/staff/", json=payload)
        flash('員工新增成功！', 'success')
        return redirect(url_for('staff_page'))
    return render_template('add_staff.html')

@app.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    # Only Admin can edit staff
    if session.get('user') != 'Admin':
        flash('權限不足：只有超級管理員可以編輯員工資料', 'danger')
        return redirect(url_for('staff_page'))
    
    if request.method == 'POST':
        payload = {
            "stName": request.form['stName'],
            "stDept": request.form['stDept'],
            "stTitle": request.form.get('stTitle', ''),
            "stPhone": request.form.get('stPhone', ''),
            "stEmail": request.form.get('stEmail', ''),
            "username": request.form['username'],
            "password": request.form['password'],
            "is_manager": request.form.get('is_manager') == '1'
        }
        try:
            response = requests.put(f"{API_BASE_URL}/staff/{staff_id}", json=payload)
            if response.status_code == 200:
                flash('員工資料更新成功！', 'success')
            elif response.status_code == 403:
                flash(response.json().get('detail', '無權限執行此操作'), 'danger')
            else:
                flash('更新失敗！', 'danger')
        except Exception as e:
            flash(f'錯誤：{str(e)}', 'danger')
        return redirect(url_for('staff_page'))
    
    # GET: 顯示編輯表單
    try:
        response = requests.get(f"{API_BASE_URL}/staff/{staff_id}")
        if response.status_code == 200:
            staff = response.json()
            return render_template('edit_staff.html', staff=staff)
        else:
            flash('找不到該員工', 'danger')
            return redirect(url_for('staff_page'))
    except:
        flash('無法連接 API', 'danger')
        return redirect(url_for('staff_page'))


@app.route('/staff/delete/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    # Only Admin can delete staff
    if session.get('user') != 'Admin':
        flash('權限不足：只有超級管理員可以刪除員工', 'danger')
        return redirect(url_for('staff_page'))
    
    try:
        requests.delete(f"{API_BASE_URL}/staff/{staff_id}")
    except:
        pass
    return redirect(url_for('staff_page'))


# ==========================================
# 5. 進貨單管理 (Inbound)
# ==========================================
@app.route('/inbound')
def inbound_page():
    try:
        response = requests.get(f"{API_BASE_URL}/inbound/")
        if response.status_code == 200:
            inbound_list = response.json()
        else:
            inbound_list = []
            flash('無法取得進貨單資料', 'danger')
    except:
        inbound_list = []
        flash('連線後端伺服器失敗', 'danger')
    return render_template('inbound.html', inbound_list=inbound_list)

@app.route('/inbound/add', methods=['GET', 'POST'])
def add_inbound():
    if request.method == 'POST':
        product_ids = request.form.getlist('product_ids[]')
        quantities = request.form.getlist('quantities[]')
        warehouse_ids = request.form.getlist('warehouse_ids[]')

        details_payload = []
        for i in range(len(product_ids)):
            details_payload.append({
                "ProductID": int(product_ids[i]),
                "idQuantity": int(quantities[i]),
                "WarehouseID": int(warehouse_ids[i])
            })

        payload = {
            "ioDate": request.form['ioDate'],
            "SupplierID": int(request.form['SupplierID']),
            "StaffID": session.get('staff_id'), # Auto-fill from session
            "details": details_payload  
        }

        try:
            response = requests.post(f"{API_BASE_URL}/inbound/", json=payload)
            if response.status_code == 201:
                flash('進貨單建立成功！', 'success')
                return redirect(url_for('inbound_page'))
            else:
                flash(f'建立失敗：{response.text}', 'danger')
        except Exception as e:
            flash(f'連線錯誤：{str(e)}', 'danger')

    # GET: 準備選單資料
    products, suppliers, warehouses, staff_list = [], [], [], []
    try:
        products = requests.get(f"{API_BASE_URL}/products/", timeout=5).json()
        suppliers = requests.get(f"{API_BASE_URL}/suppliers/", timeout=5).json()
        warehouses = requests.get(f"{API_BASE_URL}/warehouse/", timeout=5).json()
        staff_list = requests.get(f"{API_BASE_URL}/staff/").json()
    except:
        pass

    return render_template('add_inbound.html', 
                         products=products, 
                         suppliers=suppliers, 
                         warehouses=warehouses, 
                         staff_list=staff_list)

@app.route('/inbound/delete/<int:inbound_id>', methods=['POST'])
def delete_inbound(inbound_id):
    try:
        requests.delete(f"{API_BASE_URL}/inbound/{inbound_id}")
    except:
        flash('刪除失敗', 'danger')
    return redirect(url_for('inbound_page'))


# ==========================================
# 6. 領料單管理 (Requisitions) - 複數版
# ==========================================
@app.route('/requisitions')  # <--- 網址改成有 s
def requisition_page():
    try:
        response = requests.get(f"{API_BASE_URL}/requisitions/")
        if response.status_code == 200:
            req_list = response.json()
        else:
            req_list = []
            flash('無法取得領料單資料', 'danger')
    except:
        req_list = []
        flash('連線後端伺服器失敗', 'danger')
    
    # 讀取 requisitions.html (複數)
    return render_template('requisitions.html', req_list=req_list)

@app.route('/requisitions/add', methods=['GET', 'POST'])
def add_requisition():
    if request.method == 'POST':
        # 1. 讀取陣列資料
        product_ids = request.form.getlist('product_ids[]')
        quantities = request.form.getlist('quantities[]')
        warehouse_ids = request.form.getlist('warehouse_ids[]')

        # 2. 組合 details 列表
        details_payload = []
        for i in range(len(product_ids)):
            details_payload.append({
                "ProductID": int(product_ids[i]),
                "rdQuantity": int(quantities[i]), # 注意：領料單的欄位是 rdQuantity
                "WarehouseID": int(warehouse_ids[i])
            })

        # 3. 建立主單 Payload
        payload = {
            "reDate": request.form['reDate'],
            "reReason": request.form['reReason'],
            "StaffID": session.get('staff_id'), # Auto-fill from session
            "details": details_payload
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/requisitions/", json=payload)
            if response.status_code == 201:
                flash(f'領料單建立成功！共包含 {len(details_payload)} 筆商品。', 'success')
                return redirect(url_for('requisition_page'))
            else:
                flash(f'建立失敗：{response.text}', 'danger')
        except Exception as e:
            flash(f'連線錯誤：{str(e)}', 'danger')

    # GET: 準備選單資料 (保持不變)
    products, warehouses, staff_list = [], [], []
    try:
        products = requests.get(f"{API_BASE_URL}/products/", timeout=5).json()
        warehouses = requests.get(f"{API_BASE_URL}/warehouse/", timeout=5).json()
        staff_list = requests.get(f"{API_BASE_URL}/staff/").json()
    except:
        pass

    return render_template('add_requisitions.html', 
                         products=products, 
                         warehouses=warehouses, 
                         staff_list=staff_list)

@app.route('/requisitions/delete/<int:req_id>', methods=['POST']) # <--- 網址改成有 s
def delete_requisition(req_id):
    try:
        requests.delete(f"{API_BASE_URL}/requisitions/{req_id}")
        flash('領料單已刪除', 'success')
    except:
        flash('刪除失敗', 'danger')
    return redirect(url_for('requisition_page'))


# ==========================================
# 5. 商品管理 (Product)
# ==========================================
@app.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if request.method == 'POST':
        payload = {
            "prName": request.form['prName'],
            "prCategory": request.form['prCategory'],
            "prSpec": request.form.get('prSpec', '')
        }
        try:
            response = requests.put(f"{API_BASE_URL}/products/{product_id}", json=payload)
            if response.status_code == 200:
                flash('商品資料更新成功！', 'success')
            else:
                flash('更新失敗！', 'danger')
        except Exception as e:
            flash(f'錯誤：{str(e)}', 'danger')
        return redirect('/product')
    
    # GET: 顯示編輯表單
    try:
        response = requests.get(f"{API_BASE_URL}/products/{product_id}")
        if response.status_code == 200:
            product = response.json()
            return render_template('edit_product.html', product=product)
        else:
            flash('找不到該商品', 'danger')
            return redirect('/product')
    except:
        flash('無法連接 API', 'danger')
        return redirect('/product')


# ==========================================
# 6. 倉庫管理 (Warehouse)
# ==========================================
@app.route('/warehouse/edit/<int:warehouse_id>', methods=['GET', 'POST'])
def edit_warehouse(warehouse_id):
    if request.method == 'POST':
        payload = {
            "waName": request.form['waName'],
            "waLocation": request.form.get('waLocation', '')
        }
        try:
            response = requests.put(f"{API_BASE_URL}/warehouse/{warehouse_id}", json=payload)
            if response.status_code == 200:
                flash('倉庫資料更新成功！', 'success')
            else:
                flash('更新失敗！', 'danger')
        except Exception as e:
            flash(f'錯誤：{str(e)}', 'danger')
        return redirect('/warehouse')
    
    # GET: 顯示編輯表單
    try:
        response = requests.get(f"{API_BASE_URL}/warehouse/{warehouse_id}")
        if response.status_code == 200:
            warehouse = response.json()
            return render_template('edit_warehouse.html', warehouse=warehouse)
        else:
            flash('找不到該倉庫', 'danger')
            return redirect('/warehouse')
    except:
        flash('無法連接 API', 'danger')
        return redirect('/warehouse')

# ==========================================
# 7. 供應商管理 (Supplier)
# ==========================================
@app.route('/supplier/edit/<int:supplier_id>', methods=['GET', 'POST'])
def edit_supplier(supplier_id):
    if request.method == 'POST':
        payload = {
            "suName": request.form['suName'],
            "suPhone": request.form.get('suPhone', ''),
            "suAddress": request.form.get('suAddress', '')
        }
        try:
            response = requests.put(f"{API_BASE_URL}/suppliers/{supplier_id}", json=payload)
            if response.status_code == 200:
                flash('供應商資料更新成功！', 'success')
            else:
                flash('更新失敗！', 'danger')
        except Exception as e:
            flash(f'錯誤：{str(e)}', 'danger')
        return redirect('/supplier')
    
    # GET: 顯示編輯表單
    try:
        response = requests.get(f"{API_BASE_URL}/suppliers/{supplier_id}")
        if response.status_code == 200:
            supplier = response.json()
            return render_template('edit_supplier.html', supplier=supplier)
        else:
            flash('找不到該供應商', 'danger')
            return redirect('/supplier')
    except:
        flash('無法連接 API', 'danger')
        return redirect('/supplier')


# ==========================================
# 8. AI Agent
# ==========================================
@app.route('/ai-agent')
def ai_agent_page():
    return render_template('ai_agent.html')

@app.route('/ai-agent/ask', methods=['POST'])
def ai_agent_ask():
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return {"error": "No question provided"}, 400
        
    try:
        # Call FastAPI Backend
        # Note: API_BASE_URL ends with /api/v1
        response = requests.post(f"{API_BASE_URL}/ai/query", json={"question": question}, timeout=30)
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

# ==========================================
# 啟動伺服器
# ==========================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)