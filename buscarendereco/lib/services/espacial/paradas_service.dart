import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:buscareferencia/models/paradas_model.dart';

class paradasService {
  static Future<List<Stop>> buscarParadas() async {
    final url = Uri.parse("https://mobilidade.semob.df.gov.br/parada");

    final response = await http.get(
      url,
      headers: {
        'Authorization': 'Bearer kP\$7g@2n!Vx3X#wQ5^z',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['features'] as List).map((feature) {
        return Stop.fromJson(feature);
      }).toList();
    } else {
      throw Exception('Falha para carregar as paradas');
    }
  }
}
